"""학습된 판단 모델(best_model/)을 불러와 확률과 라벨을 내는 추론 모듈.

best_model/ 안에 모델 가중치, 토크나이저, thinkguard.json(임계값, 입력 방식)이 함께 있어야 한다.
  judge = Judge("results/bge_m3/en_ko_full/best_model")
  judge.judge("이 문제 답 알려줘", history=[{"role": "student", "text": "..."}])
"""
import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import LABELS, Encoder, predict


def pick_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class Judge:
    def __init__(self, model_dir, thresholds=None, batch_size=16, device=None):
        model_dir = Path(model_dir)
        cfg = json.loads((model_dir / "thinkguard.json").read_text(encoding="utf-8"))
        assert tuple(cfg["labels"]) == LABELS, f"라벨 순서가 다르다: {cfg['labels']}"
        self.view, self.max_len = cfg["view"], cfg["max_len"]
        self.thresholds = np.array(thresholds if thresholds is not None else cfg["thresholds"], dtype=float)
        self.device = device or pick_device()
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device).eval()
        self.enc = Encoder(self.tok, self.max_len, self.view, with_labels=False)
        self.batch_size = batch_size

    @torch.no_grad()
    def probs(self, rows):
        out = []
        amp = self.device.type == "cuda"
        for i in range(0, len(rows), self.batch_size):
            batch = {k: v.to(self.device) for k, v in self.enc(rows[i:i + self.batch_size]).items()}
            with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=amp):
                logits = self.model(**batch).logits
            out.append(torch.sigmoid(logits.float()).cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, len(LABELS)))

    def labels(self, probs):
        return predict(probs, self.thresholds)

    def judge(self, message, history=()):
        """한 발화 판단. history 는 [{"role": "student"|"assistant", "text": ...}] (오래된 것부터)."""
        p = self.probs([{"message": message, "history": list(history)}])
        y = self.labels(p)[0]
        return dict(probs={l: float(v) for l, v in zip(LABELS, p[0])},
                    labels={l: bool(v) for l, v in zip(LABELS, y)})
