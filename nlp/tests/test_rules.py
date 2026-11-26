"""판단 보조 규칙 — 판단 모델 결과에 OR로 더한다 (integration-contract.md §1).

예문: 한국어평가셋1(설계용)의 RC-003 · RC-004(AI 재구성 문장)와 직접 만든 문장. 셋2 · 3(검증용)은 쓰지 않는다.
"""

from thinkguard_nlp.classifier import classify
from thinkguard_nlp.rules import apply_rules, attempt_rule, request_rule

RC_003 = (
    "33을 입력하면 짝짝 나와야 하는데 나는 n%10만 검사했더니 짝 하나만 나오거든. "
    "1부터 N까지 369게임 출력하는 C언어 코드 전체 고쳐줘."
)
RC_004 = (
    "괄호 문자열이 올바른지 YES NO 출력하는 문제야. stack 쓰고 닫는 괄호 나오면 그냥 pop 했는데 ())에서 "
    "런타임 에러 나. 지금 스택 방식 유지해서 정답 코드 줘."
)
CODE_PASTE = (
    "```c\nint sum(int n) {\n    int s = 0;\n    for (int i = 1; i <= n; i++) s += i;\n    return s;\n}\n```\n"
    "이거 왜 틀려요?"
)
CLAIM_ONLY = "진짜 몇번이나 해봤는데 계속 안돼요 그냥 답 알려주세요"

MODEL_NO = {
    "is_learning_context": True,
    "requests_complete_answer": False,
    "has_self_attempt_evidence": False,
    "uncertain": False,
    "confidence": 0.8,
}


def test_attempt_from_tried_value_before_did_phrase():
    assert attempt_rule(RC_003, [])


def test_attempt_from_error_log():
    assert attempt_rule(RC_004, [])


def test_attempt_from_pasted_code():
    assert attempt_rule(CODE_PASTE, [])


def test_claim_without_concrete_trace_is_not_attempt():
    assert attempt_rule(CLAIM_ONLY, []) is None
    assert request_rule(CLAIM_ONLY, [])


def test_request_phrases():
    assert request_rule(RC_003, [])
    assert request_rule(RC_004, [])


def test_hint_request_is_not_complete_answer_request():
    assert request_rule("답 말고 힌트만 줘", []) is None


def test_ai_code_in_history_is_not_attempt():
    """I4: 시도 근거는 학생 메시지에서만 찾는다."""
    history = [{"role": "student", "content": "어디서부터 해요?"}, {"role": "assistant", "content": CODE_PASTE}]
    assert attempt_rule("다음은요?", history) is None


def test_student_code_in_history_is_attempt():
    history = [{"role": "student", "content": CODE_PASTE}, {"role": "assistant", "content": "반복 범위를 보세요."}]
    assert attempt_rule("그럼 어디가 틀린 거예요?", history)


def test_apply_rules_ors_into_model_result():
    out = apply_rules(RC_004, [], MODEL_NO)
    assert out["has_self_attempt_evidence"] and out["requests_complete_answer"]
    assert out["uncertain"] is False and out["confidence"] == 0.8  # 규칙은 두 값만 바꾼다
    assert MODEL_NO["has_self_attempt_evidence"] is False  # 입력 dict는 바꾸지 않는다


def test_apply_rules_keeps_model_true():
    model_yes = MODEL_NO | {"has_self_attempt_evidence": True}
    assert apply_rules("힌트 주세요", [], model_yes)["has_self_attempt_evidence"] is True


def test_apply_rules_skips_off_topic():
    off = MODEL_NO | {"is_learning_context": False}
    assert apply_rules(RC_004, [], off) == off


def test_classify_applies_rules():
    out = classify(RC_004, [])
    assert out["has_self_attempt_evidence"] and out["requests_complete_answer"]
