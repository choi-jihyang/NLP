"""판단 모델 스크립트들이 같이 쓰는 데이터 로드, 입력 구성, 정책, 평가 지표."""
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

LABELS = ("is_learning_context", "requests_complete_answer", "has_self_attempt_evidence")
SHORT = {"is_learning_context": "learning", "requests_complete_answer": "request", "has_self_attempt_evidence": "attempt"}


def load(dirs, split, limit=0):
    """dirs 의 <split>.jsonl 을 합쳐 읽는다. 번역 실패 행(translation_ok=false)은 뺀다."""
    rows = []
    for d in dirs:
        p = Path(d) / f"{split}.jsonl"
        if not p.exists():
            continue
        part = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        part = [r for r in part if r.get("translation_ok", True)]
        rows += part[:limit] if limit else part
    return rows


def history_text(r):
    return "\n".join(("학생" if h["role"] == "student" else "AI") + ": " + h["text"] for h in r["history"])


class Encoder:
    """판단 모델 입력: 현재 발화를 첫 문장, 이전 대화를 둘째 문장으로 넣는다 (학습·추론 공통)."""

    def __init__(self, tokenizer, max_len, view, with_labels=True):
        self.tok, self.max_len, self.view, self.with_labels = tokenizer, max_len, view, with_labels

    def __call__(self, rows):
        import torch
        msgs = [r["message"] or "(빈 메시지)" for r in rows]
        if self.view == "message":
            enc = self.tok(msgs, truncation=True, max_length=self.max_len, padding=True, return_tensors="pt")
        else:
            hist = [history_text(r) or "(이전 대화 없음)" for r in rows]
            enc = self.tok(msgs, hist, truncation="longest_first", max_length=self.max_len,
                           padding=True, return_tensors="pt")
        if self.with_labels:
            enc["labels"] = torch.tensor(labels_of(rows), dtype=torch.float)
        return enc


def labels_of(rows):
    return np.array([[r["labels"][l] for l in LABELS] for r in rows], dtype=int)


def apply_policy(pred):
    """학습 맥락이 아니면 나머지 두 라벨도 false (학습 데이터와 같은 규칙)."""
    pred = pred.copy()
    pred[pred[:, 0] == 0, 1:] = 0
    return pred


def best_threshold(y, p, pos_label=1):
    best_t, best_f = 0.5, -1
    for t in np.arange(0.05, 0.96, 0.01):
        f = f1_score(y, (p >= t).astype(int), pos_label=pos_label, zero_division=0)
        if f > best_f:
            best_t, best_f = float(t), f
    return best_t


def tune_thresholds(y, probs):
    """learning 은 드문 false 를 잘 찾도록 false 클래스 F1 기준으로, 나머지는 true 클래스 F1 기준으로."""
    return np.array([best_threshold(y[:, 0], probs[:, 0], pos_label=0),
                     best_threshold(y[:, 1], probs[:, 1]),
                     best_threshold(y[:, 2], probs[:, 2])])


def predict(probs, thresholds):
    return apply_policy((probs >= thresholds).astype(int))


def report(y, pred):
    out = {}
    for i, l in enumerate(LABELS):
        out[l] = dict(f1=f1_score(y[:, i], pred[:, i], zero_division=0),
                      precision=precision_score(y[:, i], pred[:, i], zero_division=0),
                      recall=recall_score(y[:, i], pred[:, i], zero_division=0),
                      support=int(y[:, i].sum()))
    out["macro_f1"] = float(np.mean([out[l]["f1"] for l in LABELS]))
    # 학습 맥락은 98%가 true라서 F1(true)은 늘 0.99 근처다. 의미 있는 건 드문 false(인사·잡담)를 찾는 능력.
    out["is_learning_context"]["f1_false_class"] = f1_score(y[:, 0], pred[:, 0], pos_label=0, zero_division=0)
    out["macro_f1_request_attempt"] = float(np.mean([out[l]["f1"] for l in LABELS[1:]]))
    # 서비스 관점: 답을 요청했는데 시도가 없는 학생에게 '시도 있음'으로 판단해 답/다음 단계를 열어주는 경우
    req_no_try = (y[:, 1] == 1) & (y[:, 2] == 0)
    req_try = (y[:, 1] == 1) & (y[:, 2] == 1)
    out["false_unlock"] = dict(count=int((req_no_try & (pred[:, 2] == 1)).sum()), of=int(req_no_try.sum()))
    out["unnecessary_check"] = dict(count=int((req_try & (pred[:, 2] == 0)).sum()), of=int(req_try.sum()))
    out["exact_match"] = float((y == pred).all(axis=1).mean())
    # 팀 공통 비교용: 라벨마다 true·false F1 평균(macro)을 내고 라벨 3개를 다시 평균
    out["mean_label_macro_f1"] = float(np.mean([f1_score(y[:, i], pred[:, i], average="macro", zero_division=0)
                                                for i in range(len(LABELS))]))
    return out


def selection_score(rep):
    """모델 선택용 단일 점수: request F1, attempt F1, learning=false F1 의 평균."""
    return float(np.mean([rep["requests_complete_answer"]["f1"], rep["has_self_attempt_evidence"]["f1"],
                          rep["is_learning_context"]["f1_false_class"]]))


def fmt(rep):
    cells = [f"{SHORT[l]} F1 {rep[l]['f1']:.3f} (P {rep[l]['precision']:.2f} / R {rep[l]['recall']:.2f})" for l in LABELS[1:]]
    fu, uc = rep["false_unlock"], rep["unnecessary_check"]
    return (" | ".join(cells) + f" | learning=false F1 {rep['is_learning_context']['f1_false_class']:.3f}"
            f"\n    request·attempt 평균 F1 {rep['macro_f1_request_attempt']:.3f} | "
            f"mean_label_macro_f1 {rep['mean_label_macro_f1']:.3f} | exact {rep['exact_match']:.3f} | "
            f"false_unlock {fu['count']}/{fu['of']} | unnecessary_check {uc['count']}/{uc['of']}")
