"""연동 계약 출력 변환 테스트 (모델 없이 실행)."""

from thinkguard_nlp.model import HISTORY_MSGS, history_text, to_contract

TH = [0.05, 0.55, 0.73]
KEYS = {"is_learning_context", "requests_complete_answer", "has_self_attempt_evidence", "uncertain", "confidence"}


def test_output_has_contract_fields():
    out = to_contract([0.99, 0.99, 0.01], TH)
    assert set(out) == KEYS
    assert isinstance(out["confidence"], float) and 0.0 <= out["confidence"] <= 1.0


def test_answer_request_without_attempt_is_confident():
    out = to_contract([0.99, 0.99, 0.01], TH)
    assert out["requests_complete_answer"] and not out["has_self_attempt_evidence"]
    assert out["confidence"] >= 0.5


def test_not_learning_forces_other_labels_false():
    out = to_contract([0.01, 0.99, 0.99], TH)
    assert not out["is_learning_context"]
    assert not out["requests_complete_answer"] and not out["has_self_attempt_evidence"]


def test_attempt_near_threshold_is_low_confidence():
    # 답 요청이 확실해도 시도 근거 확률이 임계값 근처면 되묻기 대상(confidence < 0.5)
    out = to_contract([0.99, 0.99, 0.70], TH)
    assert out["confidence"] < 0.5


def test_attempt_ignored_when_not_requesting():
    # 답 요청이 아니면 시도 근거는 정책에 안 쓰이므로 confidence 에 영향 없음
    out = to_contract([0.99, 0.01, 0.73], TH)
    assert out["confidence"] >= 0.5


def test_history_uses_contract_keys_and_keeps_recent_turns():
    hist = [{"role": "student" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(6)]
    text = history_text(hist)
    assert text.splitlines() == ["학생: m2", "AI: m3", "학생: m4", "AI: m5"][-HISTORY_MSGS:]
