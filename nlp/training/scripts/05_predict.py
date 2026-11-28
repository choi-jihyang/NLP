"""5단계: 학습된 판단 모델로 한 split 전체의 확률을 뽑는다.

06_tune_policy.py 로 운영 임계값을 정하려면 valid 확률이 필요하다.
(04 스크립트 최신 버전은 학습 때 valid_probs.npy 를 같이 저장하므로, 그 결과가 있으면 이 단계는 건너뛴다.)
한국어 실사용 평가셋도 같은 jsonl 형식으로 만들어 두면 이 스크립트로 평가한다.

사용 예:
  python scripts/05_predict.py --model-dir results/bge_m3/en_ko_full/best_model --data-dirs data/joined data/ko --split valid
  python scripts/05_predict.py --model-dir ... --data-dirs data/ko_eval --split test --out-dir results/ko_eval
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

from common import fmt, labels_of, load, report
from judge import Judge

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-dir", required=True, help="best_model 폴더 (thinkguard.json 포함)")
    ap.add_argument("--data-dirs", nargs="+", default=[str(ROOT / "data/joined"), str(ROOT / "data/ko")])
    ap.add_argument("--split", default="valid")
    ap.add_argument("--out-dir", default=None, help="기본: model-dir 의 상위 폴더")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = load(args.data_dirs, args.split, args.limit)
    if not rows:
        raise SystemExit(f"{args.split}.jsonl 을 찾지 못했다: {args.data_dirs} (--data-dirs 경로 확인)")
    out = Path(args.out_dir or Path(args.model_dir).parent)
    out.mkdir(parents=True, exist_ok=True)
    judge = Judge(args.model_dir, batch_size=args.batch_size)
    print(f"device={judge.device} | {args.split} {len(rows)}행 | view={judge.view} max_len={judge.max_len}")

    t0 = time.time()
    probs = judge.probs(rows)
    print(f"추론 {time.time() - t0:.0f}s")
    np.save(out / f"{args.split}_probs.npy", probs)
    (out / f"{args.split}_ids.json").write_text(
        json.dumps([r["id"] + ":" + r.get("lang", "en") for r in rows]), encoding="utf-8")

    if all("labels" in r for r in rows):
        y, pred = labels_of(rows), judge.labels(probs)
        langs = sorted({r.get("lang", "en") for r in rows})
        for lang in langs + (["all"] if len(langs) > 1 else []):
            idx = [i for i, r in enumerate(rows) if lang == "all" or r.get("lang", "en") == lang]
            print(f"  {args.split}[{lang}] ({len(idx)}행) {fmt(report(y[idx], pred[idx]))}")
    print(f"저장: {out}/{args.split}_probs.npy, {args.split}_ids.json")


if __name__ == "__main__":
    main()
