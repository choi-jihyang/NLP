"""3단계: TF-IDF + Logistic Regression 기준선.

라벨 3개를 각각 이진 분류기로 학습한다 (one-vs-rest multi-label).
- 임계값은 valid 셋에서 정하고 test 셋에는 한 번만 적용한다 (common.tune_thresholds).
- 정책 규칙: is_learning_context=false로 예측하면 나머지 두 라벨도 false.
- 입력 방식 두 가지를 비교한다: message(현재 발화만), full(현재 발화 + 이전 대화).

사용 예:
  python scripts/03_baseline_tfidf.py                                                # 영어 데이터
  python scripts/03_baseline_tfidf.py --data-dirs data/joined data/ko --tag en_ko    # 번역 후 영어+한국어
"""
import argparse
import json
import random
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from common import LABELS, SHORT, fmt, history_text, labels_of, load, predict, report, tune_thresholds

MAX_CHARS = 4000


def format_input(r, view):
    msg = r["message"][:MAX_CHARS]
    if view == "message":
        return msg
    hist = history_text(r)
    return f"[CURRENT] {msg}\n[HISTORY]\n{hist[:MAX_CHARS] if hist else '(none)'}"


def run(train, valid, test, view):
    texts = {k: [format_input(r, view) for r in rows] for k, rows in
             (("train", train), ("valid", valid), ("test", test))}
    word = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=200_000, sublinear_tf=True)
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, max_features=300_000, sublinear_tf=True)
    X = {"train": hstack([word.fit_transform(texts["train"]), char.fit_transform(texts["train"])]).tocsr()}
    for k in ("valid", "test"):
        X[k] = hstack([word.transform(texts[k]), char.transform(texts[k])]).tocsr()
    Y = {k: labels_of(v) for k, v in (("train", train), ("valid", valid), ("test", test))}

    probs = {"valid": [], "test": []}
    for i in range(len(LABELS)):
        clf = LogisticRegression(class_weight="balanced", max_iter=2000, C=4.0)
        clf.fit(X["train"], Y["train"][:, i])
        for k in ("valid", "test"):
            probs[k].append(clf.predict_proba(X[k])[:, 1])
    probs = {k: np.stack(v, 1) for k, v in probs.items()}
    th = tune_thresholds(Y["valid"], probs["valid"])
    pred = {k: predict(probs[k], th) for k in ("valid", "test")}
    return dict(thresholds=dict(zip(LABELS, th.tolist())),
                valid=report(Y["valid"], pred["valid"]),
                test=report(Y["test"], pred["test"])), pred["test"]


def majority(train, test):
    ytr, yte = labels_of(train), labels_of(test)
    pred = np.tile((ytr.mean(0) >= 0.5).astype(int), (len(test), 1))
    return report(yte, pred)


def save_errors(path, test, pred):
    y = labels_of(test)
    errs = []
    for idx in np.where((y != pred).any(axis=1))[0]:
        r = test[idx]
        errs.append(dict(id=r["id"], lang=r.get("lang", "en"),
                         gold={SHORT[l]: int(y[idx, i]) for i, l in enumerate(LABELS)},
                         pred={SHORT[l]: int(pred[idx, i]) for i, l in enumerate(LABELS)},
                         message=r["message"][:500],
                         prev=(r["history"][-1]["role"] + ": " + r["history"][-1]["text"][:300]) if r["history"] else ""))
    random.Random(0).shuffle(errs)
    path.write_text(json.dumps(errs[:200], ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dirs", nargs="+", default=["data/joined"])
    ap.add_argument("--test-dirs", nargs="+", default=None, help="평가 데이터 폴더 (기본: --data-dirs와 같음)")
    ap.add_argument("--views", nargs="+", default=["message", "full"])
    ap.add_argument("--tag", default="en")
    ap.add_argument("--out-dir", default="results/baseline_tfidf")
    args = ap.parse_args()

    train, valid = load(args.data_dirs, "train"), load(args.data_dirs, "valid")
    test = load(args.test_dirs or args.data_dirs, "test")
    print(f"train {len(train)} / valid {len(valid)} / test {len(test)}")

    out = Path(args.out_dir) / args.tag
    out.mkdir(parents=True, exist_ok=True)
    results = {"majority": majority(train, test)}
    print(f"\n[다수 클래스 기준선] test\n    {fmt(results['majority'])}")
    for view in args.views:
        res, pred = run(train, valid, test, view)
        results[view] = res
        print(f"\n[TF-IDF + LR, view={view}] 임계값 {', '.join(f'{SHORT[k]}={v:.2f}' for k, v in res['thresholds'].items())}")
        print(f"  valid {fmt(res['valid'])}")
        print(f"  test  {fmt(res['test'])}")
        save_errors(out / f"errors_{view}.json", test, pred)
    (out / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {out}/metrics.json, errors_*.json")


if __name__ == "__main__":
    main()
