"""6단계: 운영 임계값 정하기 (attempt 임계값의 false_unlock ↔ unnecessary_check 트레이드오프).

F1 최대 임계값은 두 실수를 같은 무게로 본다. 서비스에서는 '시도 없는 학생에게 답을 열어주는 실수(false_unlock)'가
더 비싸므로, 허용할 false_unlock 비율(--max-false-unlock)을 정하고 그 안에서 unnecessary_check 가 가장 적은
attempt 임계값을 고른다. 반드시 valid 확률로 정하고, test 에는 결과만 확인한다.

입력: 05_predict.py 또는 04 학습이 저장한 <split>_probs.npy + <split>_ids.json

사용 예:
  python scripts/06_tune_policy.py --probs-dir results/bge_m3/en_ko_full --split valid \\
      --base-thresholds results/bge_m3/en_ko_full/best_model/thinkguard.json --max-false-unlock 0.25
  # 정한 임계값으로 test 확인만:
  python scripts/06_tune_policy.py --probs-dir results/bge_m3/en_ko_full --split test --apply results/bge_m3/en_ko_full/policy_thresholds.json
"""
import argparse
import json
from pathlib import Path

import numpy as np

from common import LABELS, labels_of, load, predict, report
from policy import MODES, modes_of


def read_thresholds(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    th = d["thresholds"]
    return np.array([th[l] for l in LABELS] if isinstance(th, dict) else th, dtype=float)


def rates(y, pred):
    rep = report(y, pred)
    fu, uc = rep["false_unlock"], rep["unnecessary_check"]
    return dict(fu=fu["count"] / max(fu["of"], 1), uc=uc["count"] / max(uc["of"], 1), fu_n=fu, uc_n=uc,
                att_f1=rep["has_self_attempt_evidence"]["f1"], macro=rep["mean_label_macro_f1"])


def mode_confusion(y, pred):
    gold, guess = modes_of(y), modes_of(pred)
    m = {g: {p: 0 for p in MODES} for g in MODES}
    for g, p in zip(gold, guess):
        m[g][p] += 1
    print("\n모드 혼동표 (행=정답 모드, 열=예측 모드)")
    print(f"  {'':10s}" + "".join(f"{p:>10s}" for p in MODES) + f"{'합계':>8s}")
    for g in MODES:
        print(f"  {g:10s}" + "".join(f"{m[g][p]:>10d}" for p in MODES) + f"{sum(m[g].values()):>9d}")
    return m

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probs-dir", required=True)
    ap.add_argument("--split", default="valid")
    ap.add_argument("--data-dirs", nargs="+", default=[str(ROOT / "data/joined"), str(ROOT / "data/ko")])
    ap.add_argument("--base-thresholds", help="thinkguard.json 또는 metrics.json (learning·request 임계값은 그대로 씀)")
    ap.add_argument("--max-false-unlock", type=float, default=0.25, help="허용할 false_unlock 비율 (0~1)")
    ap.add_argument("--apply", help="이미 정한 policy_thresholds.json 을 이 split 에 적용만 한다")
    args = ap.parse_args()

    pdir = Path(args.probs_dir)
    probs = np.load(pdir / f"{args.split}_probs.npy", allow_pickle=False)
    ids = json.loads((pdir / f"{args.split}_ids.json").read_text(encoding="utf-8"))
    rows = {r["id"] + ":" + r.get("lang", "en"): r for r in load(args.data_dirs, args.split)}
    missing = [i for i in ids if i not in rows]
    assert not missing, f"데이터에 없는 id {len(missing)}개 (예: {missing[:3]}) — --data-dirs/--split 확인"
    y = labels_of([rows[i] for i in ids])
    langs = sorted({i.rsplit(":", 1)[1] for i in ids})
    lang_idx = {l: [k for k, i in enumerate(ids) if i.endswith(":" + l)] for l in langs}
    print(f"{args.split} {len(ids)}행 ({', '.join(f'{l} {len(v)}' for l, v in lang_idx.items())})")

    if args.apply:
        th = read_thresholds(args.apply)
        print(f"임계값 적용: {dict(zip(LABELS, th.round(2).tolist()))}")
        for l in langs + (["all"] if len(langs) > 1 else []):
            idx = lang_idx.get(l, list(range(len(ids))))
            r = rates(y[idx], predict(probs[idx], th))
            print(f"  [{l}] false_unlock {r['fu_n']['count']}/{r['fu_n']['of']} ({r['fu']:.0%}) | "
                  f"unnecessary_check {r['uc_n']['count']}/{r['uc_n']['of']} ({r['uc']:.0%}) | "
                  f"attempt F1 {r['att_f1']:.3f} | mean_label_macro_f1 {r['macro']:.3f}")
        mode_confusion(y, predict(probs, th))
        return

    assert args.base_thresholds, "--base-thresholds 가 필요하다 (learning·request 임계값)"
    base = read_thresholds(args.base_thresholds)
    print(f"기준 임계값: {dict(zip(LABELS, base.round(2).tolist()))}")
    print("\nattempt 임계값별 (learning·request 고정) — false_unlock: 시도 없는 답 요청을 '시도 있음'으로, "
          "unnecessary_check: 시도 있는 답 요청을 '시도 없음'으로")
    print(f"  {'t':>5s} {'false_unlock':>14s} {'unnec_check':>14s} {'att F1':>7s} {'macroF1':>8s}"
          + "".join(f" {'FU[' + l + ']':>7s}" for l in langs))
    grid = np.round(np.arange(0.05, 0.96, 0.01), 2)
    table = []
    for t in grid:
        th = base.copy(); th[2] = t
        pred = predict(probs, th)
        r = rates(y, pred)
        r["t"] = float(t)
        r["by_lang"] = {l: rates(y[i], pred[i])["fu"] for l, i in lang_idx.items()}
        table.append(r)
        if round(t * 100) % 5 == 0 or abs(t - base[2]) < 0.005:
            mark = " ← 현재(F1 최대)" if abs(t - base[2]) < 0.005 else ""
            print(f"  {t:5.2f} {r['fu_n']['count']:>5d}/{r['fu_n']['of']:<4d}({r['fu']:4.0%}) "
                  f"{r['uc_n']['count']:>5d}/{r['uc_n']['of']:<4d}({r['uc']:4.0%}) {r['att_f1']:7.3f} {r['macro']:8.3f}"
                  + "".join(f" {r['by_lang'][l]:7.0%}" for l in langs) + mark)

    ok = [r for r in table if r["fu"] <= args.max_false_unlock]
    if not ok:
        print(f"\nfalse_unlock {args.max_false_unlock:.0%} 이하를 만드는 임계값이 없다. 목표를 올리거나 모델을 개선해야 한다.")
        return
    pick = min(ok, key=lambda r: (r["uc"], r["t"]))
    th = base.copy(); th[2] = pick["t"]
    print(f"\n추천: false_unlock ≤ {args.max_false_unlock:.0%} 조건에서 unnecessary_check 최소 → attempt 임계값 {pick['t']:.2f}")
    print(f"  false_unlock {pick['fu_n']['count']}/{pick['fu_n']['of']} ({pick['fu']:.0%}) | "
          f"unnecessary_check {pick['uc_n']['count']}/{pick['uc_n']['of']} ({pick['uc']:.0%}) | "
          f"attempt F1 {pick['att_f1']:.3f} (F1 최대 {max(r['att_f1'] for r in table):.3f})")
    conf = mode_confusion(y, predict(probs, th))

    out = pdir / ("policy_thresholds.json" if args.split == "valid" else f"policy_thresholds_{args.split}.json")
    out.write_text(json.dumps(dict(
        labels=LABELS, thresholds=dict(zip(LABELS, th.tolist())), chosen_on=args.split,
        max_false_unlock=args.max_false_unlock, false_unlock=pick["fu_n"], unnecessary_check=pick["uc_n"],
        mode_confusion=conf, curve=[{k: r[k] for k in ("t", "fu", "uc", "att_f1", "macro")} for r in table],
    ), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {out}")
    if args.split != "valid":
        print("주의: valid 가 아닌 split 으로 정한 임계값이다. 미리보기로만 쓰고, 운영 임계값은 valid 로 다시 정한다.")


if __name__ == "__main__":
    main()
