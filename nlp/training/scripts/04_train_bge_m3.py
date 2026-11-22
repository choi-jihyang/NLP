"""4단계: bge-m3 파인튜닝 판단 모델 (라벨 3개 multi-label 분류).

구조: BAAI/bge-m3 인코더(XLM-RoBERTa large 기반, 다국어) + [CLS] 위 선형층 3개 출력, BCE 손실.
입력: 현재 학생 발화를 첫 문장, 이전 대화를 둘째 문장으로 넣는다 (길면 긴 쪽부터 잘라냄).
절차: epoch마다 valid로 평가 → 가장 좋은 epoch의 모델 저장 → valid로 임계값 결정 → test 셋에 한 번 적용.

사용 예 (Colab T4):
  python scripts/04_train_bge_m3.py --train-dirs data/joined data/ko --test-dirs data/joined data/ko
Mac에서 코드만 점검:
  python scripts/04_train_bge_m3.py --model intfloat/multilingual-e5-small --limit 64 --epochs 1 --max-len 128
"""
import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from common import LABELS, SHORT, Encoder, fmt, labels_of, load, predict, report, selection_score, tune_thresholds


def pick_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


@torch.no_grad()
def infer(model, loader, device, amp):
    model.eval()
    out = []
    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items() if k != "labels"}
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
            logits = model(**batch).logits
        out.append(torch.sigmoid(logits.float()).cpu().numpy())
    return np.concatenate(out)


def by_lang(rows):
    groups = {}
    for i, r in enumerate(rows):
        groups.setdefault(r.get("lang", "en"), []).append(i)
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train-dirs", nargs="+", default=["data/joined"])
    ap.add_argument("--test-dirs", nargs="+", default=None, help="valid/test 폴더 (기본: --train-dirs)")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--view", default="full", choices=["message", "full"])
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=4, help="실효 배치 = batch-size x grad-accum")
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--warmup", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--limit", type=int, default=0, help="split·폴더별 앞 N행만 (점검용)")
    ap.add_argument("--grad-checkpointing", action="store_true", help="메모리 절약 (느려짐)")
    ap.add_argument("--save-model", action="store_true", help="최고 성능 모델 가중치 저장 (bge-m3 약 2.3GB)")
    ap.add_argument("--out-dir", default="results/bge_m3")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    device = pick_device()
    amp = device.type == "cuda"
    test_dirs = args.test_dirs or args.train_dirs
    train = load(args.train_dirs, "train", args.limit)
    valid = load(test_dirs, "valid", args.limit)
    test = load(test_dirs, "test", args.limit)
    tag = args.tag or f"{'_'.join(Path(d).name for d in args.train_dirs)}_{args.view}"
    out = Path(args.out_dir) / tag
    out.mkdir(parents=True, exist_ok=True)
    print(f"device={device} amp={amp} | train {len(train)} / valid {len(valid)} / test {len(test)} | 저장 {out}")

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(LABELS), problem_type="multi_label_classification").to(device)
    if args.grad_checkpointing:
        model.gradient_checkpointing_enable()

    enc = Encoder(tok, args.max_len, args.view)
    train_loader = DataLoader(train, batch_size=args.batch_size, shuffle=True, collate_fn=enc)
    valid_loader = DataLoader(valid, batch_size=args.batch_size * 2, collate_fn=enc)
    test_loader = DataLoader(test, batch_size=args.batch_size * 2, collate_fn=enc)

    # 불균형 보정: 양성이 드문 라벨은 양성 손실에 가중치. learning 은 음성이 드물어서 1로 둔다.
    y_tr = labels_of(train)
    pos = y_tr.mean(0).clip(1e-3, 1 - 1e-3)
    pos_weight = torch.tensor([1.0] + [(1 - p) / p for p in pos[1:]], dtype=torch.float, device=device)
    neg_weight_learning = float(min((pos[0]) / (1 - pos[0]), 10.0))  # learning=false 행의 손실 가중
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="none")
    print("pos_weight", [round(x, 2) for x in pos_weight.tolist()], "| learning=false 가중", round(neg_weight_learning, 1))

    optim = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = math.ceil(len(train_loader) / args.grad_accum) * args.epochs
    sched = get_linear_schedule_with_warmup(optim, int(steps * args.warmup), steps)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    y_va, y_te = labels_of(valid), labels_of(test)
    best = dict(score=-1)
    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, total = time.time(), 0.0
        for step, batch in enumerate(train_loader, 1):
            labels = batch.pop("labels").to(device)
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                logits = model(**batch).logits
            loss = loss_fn(logits.float(), labels)
            row_w = torch.ones_like(labels)
            row_w[:, 0] = torch.where(labels[:, 0] == 0, neg_weight_learning, 1.0)
            loss = (loss * row_w).mean() / args.grad_accum
            scaler.scale(loss).backward()
            total += loss.item() * args.grad_accum
            if step % args.grad_accum == 0 or step == len(train_loader):
                scaler.unscale_(optim)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optim); scaler.update(); optim.zero_grad(); sched.step()
            if step % 100 == 0:
                print(f"  epoch {epoch} step {step}/{len(train_loader)} loss {total / step:.4f} ({time.time() - t0:.0f}s)")
        p_va = infer(model, valid_loader, device, amp)
        th = tune_thresholds(y_va, p_va)
        rep = report(y_va, predict(p_va, th))
        score = selection_score(rep)
        history.append(dict(epoch=epoch, train_loss=total / len(train_loader), valid_score=score))
        print(f"[epoch {epoch}] train loss {total / len(train_loader):.4f} | valid 선택점수 {score:.3f}\n  valid {fmt(rep)}")
        if score > best["score"]:
            best = dict(score=score, epoch=epoch, thresholds=th, p_va=p_va, p_te=infer(model, test_loader, device, amp))
            if args.save_model:
                model.save_pretrained(out / "best_model"); tok.save_pretrained(out / "best_model")

    # 최종: 최고 epoch 의 valid 임계값을 test 에 한 번 적용
    th = best["thresholds"]
    results = dict(config=vars(args), best_epoch=best["epoch"], history=history,
                   thresholds=dict(zip(LABELS, th.tolist())),
                   valid=report(y_va, predict(best["p_va"], th)), test={})
    print(f"\n최고 epoch {best['epoch']} | 임계값 {', '.join(f'{SHORT[l]}={t:.2f}' for l, t in zip(LABELS, th))}")
    for lang, idx in sorted(by_lang(test).items()):
        rep = report(y_te[idx], predict(best["p_te"][idx], th))
        results["test"][lang] = rep
        print(f"  test[{lang}] ({len(idx)}행) {fmt(rep)}")
    if len(by_lang(test)) > 1:
        results["test"]["all"] = report(y_te, predict(best["p_te"], th))
    (out / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if args.save_model:  # 추론할 때 같은 입력 방식과 임계값을 쓰도록 함께 저장
        (out / "best_model" / "thinkguard.json").write_text(json.dumps(dict(
            labels=LABELS, thresholds=th.tolist(), view=args.view, max_len=args.max_len), indent=2), encoding="utf-8")
    np.save(out / "test_probs.npy", best["p_te"])
    np.save(out / "valid_probs.npy", best["p_va"])  # 06_tune_policy.py 로 운영 임계값을 정할 때 쓴다
    (out / "valid_ids.json").write_text(json.dumps([r["id"] + ":" + r.get("lang", "en") for r in valid]), encoding="utf-8")
    (out / "test_ids.json").write_text(json.dumps([r["id"] + ":" + r.get("lang", "en") for r in test]), encoding="utf-8")
    print(f"저장: {out}/metrics.json")


if __name__ == "__main__":
    main()
