"""bge-m3 판단 모델 로딩·추론과 연동 계약 형식 변환.

모델 폴더(best_model/)에는 가중치, 토크나이저, thinkguard.json(임계값·입력 방식)이 함께 있어야 한다.
입력 형식은 학습 때(nlp/training/scripts/common.py Encoder)와 같아야 한다:
  첫 문장 = 현재 학생 발화, 둘째 문장 = 이전 대화 최근 4개("학생: ..." / "AI: ..."), 각 800자로 자름.
"""

import json
from pathlib import Path
from typing import Any

LABELS = ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence")
HISTORY_MSGS = 4
HISTORY_MAX_CHARS = 800
# 판단 여유(margin)가 이 값보다 작으면 confidence < 0.5 가 되어 백엔드가 되묻기(ASK_ATTEMPT)로 보낸다.
# valid 기준 약 9% 가 되묻기로 간다. 더 자주 되묻게 하려면 백엔드 CLASSIFIER_MIN_CONFIDENCE 를 올린다.
MARGIN_AT_HALF_CONFIDENCE = 0.2


def _truncate(text: str, max_chars: int = HISTORY_MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.7)
    return text[:head] + "\n...[중략]...\n" + text[-(max_chars - head) :]


def history_text(history: list[dict[str, str]]) -> str:
    """연동 계약 history([{role, content}], 오래된 순) → 학습 때와 같은 문자열."""
    lines = []
    for turn in history[-HISTORY_MSGS:]:
        who = "학생" if turn["role"] == "student" else "AI"
        lines.append(f"{who}: {_truncate(turn['content'])}")
    return "\n".join(lines)


def margins(probs: list[float], thresholds: list[float]) -> list[float]:
    """라벨별 판단 여유: 임계값에서 0, 확률 0 또는 1 끝에서 1."""
    out = []
    for p, t in zip(probs, thresholds, strict=True):
        out.append((p - t) / (1 - t) if p >= t else (t - p) / t)
    return out


def to_contract(probs: list[float], thresholds: list[float]) -> dict[str, Any]:
    """라벨별 확률 → 연동 계약 출력 (docs/spec/integration-contract.md).

    - 학습 맥락이 아니면 나머지 두 라벨은 false (학습 데이터와 같은 규칙).
    - confidence 는 정책 결정에 실제로 쓰인 라벨들의 판단 여유 중 가장 작은 값으로 정한다.
      (학습 맥락 → 학습 맥락이면 답 요청 → 답 요청이면 시도 근거)
      여유 MARGIN_AT_HALF_CONFIDENCE 가 confidence 0.5 에 오도록 이어 붙인다.
    """
    learning = probs[0] >= thresholds[0]
    request = learning and probs[1] >= thresholds[1]
    attempt = learning and probs[2] >= thresholds[2]
    m = margins(probs, thresholds)
    used = [m[0]] + ([m[1]] if learning else []) + ([m[2]] if request else [])
    margin = min(used)
    if margin < MARGIN_AT_HALF_CONFIDENCE:
        confidence = 0.5 * margin / MARGIN_AT_HALF_CONFIDENCE
    else:
        confidence = 0.5 + 0.5 * (margin - MARGIN_AT_HALF_CONFIDENCE) / (1 - MARGIN_AT_HALF_CONFIDENCE)
    return {
        "is_learning_context": bool(learning),
        "requests_complete_answer": bool(request),
        "has_self_attempt_evidence": bool(attempt),
        "uncertain": False,
        "confidence": round(float(min(max(confidence, 0.0), 1.0)), 4),
    }


class Judge:
    """판단 모델. 생성 비용이 크므로(약 2.3GB) 프로세스당 한 번만 만든다."""

    def __init__(self, model_dir: str | Path, device: str | None = None):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_dir = Path(model_dir)
        cfg_path = model_dir / "thinkguard.json"
        if not cfg_path.exists():
            raise FileNotFoundError(
                f"판단 모델이 없습니다: {model_dir} (best_model 폴더를 넣거나 THINKGUARD_MODEL_DIR 를 지정하세요)"
            )
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        if tuple(cfg["labels"]) != LABELS:
            raise ValueError(f"라벨 순서가 다릅니다: {cfg['labels']}")
        self.thresholds = [float(t) for t in cfg["thresholds"]]
        self.view, self.max_len = cfg["view"], int(cfg["max_len"])
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self._torch = torch
        self.device = torch.device(device)
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device).eval()

    def probs(self, message: str, history: list[dict[str, str]]) -> list[float]:
        torch = self._torch
        msg = message or "(빈 메시지)"
        if self.view == "message":
            enc = self.tok(msg, truncation=True, max_length=self.max_len, return_tensors="pt")
        else:
            hist = history_text(history) or "(이전 대화 없음)"
            enc = self.tok(msg, hist, truncation="longest_first", max_length=self.max_len, return_tensors="pt")
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            logits = self.model(**enc).logits
        return torch.sigmoid(logits.float())[0].cpu().tolist()

    def classify(self, message: str, history: list[dict[str, str]]) -> dict[str, Any]:
        return to_contract(self.probs(message, history), self.thresholds)
