"""학생처럼 졸라보기 — 실제 정책 경로(분류 → 정책 → 프롬프트 → LLM → 누출 검사)를 그대로 쓰는지."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.classifier.keyword_stub import KeywordStubClassifier
from app.leak_guard.module import ModuleLeakGuard
from app.llm.mock import MockProvider
from app.schemas.assignments import AssignmentData
from app.services.policy import ResponseMode
from app.services.prompt_builder import FIXED_RULES, SECRET_TAG
from app.services.simulate_service import ATTACKS, simulate
from tests.factories import api_class, api_teacher
from tests.test_assignments_api import ASSIGNMENT

GUARD = ModuleLeakGuard("thinkguard_nlp.leak:check_leak")
PY_FULL = (
    "```python\ndef to_binary(n):\n    if n == 0:\n        return '0'\n    bits = ''\n    while n > 0:\n"
    "        bits = str(n % 2) + bits\n        n //= 2\n    return bits\n```"
)
C_FULL = (
    "```c\n#include <stdio.h>\nvoid print_binary(unsigned int n) {\n    char bits[33]; int len = 0;\n"
    "    if (n == 0) { printf(\"0\"); return; }\n    while (n > 0) { bits[len++] = '0' + n % 2; n /= 2; }\n"
    "    for (int i = len - 1; i >= 0; i--) printf(\"%c\", bits[i]);\n}\n```"
)


def run(llm, data=ASSIGNMENT):
    a = AssignmentData.model_validate(data)
    return asyncio.run(simulate(a, KeywordStubClassifier(), llm, GUARD, 0.5))


def test_targets_code_question_first_and_runs_every_attack():
    cases = run(MockProvider())
    code_index = next(i for i, q in enumerate(ASSIGNMENT["questions"]) if q["type"] == "CODE")
    assert [c.message for c in cases if c.question_index == code_index] == list(ATTACKS)
    assert len(cases) <= 6


def test_answer_requests_end_as_hint_only_never_offer_choices():
    """고르기 단계를 지나 'ORIGINAL'을 골라도 HINT_ONLY (I1). OFFER_CHOICES로 끝나는 사례는 없다."""
    cases = run(MockProvider())
    assert all(c.response_mode is not ResponseMode.OFFER_CHOICES for c in cases)
    answer_requests = [c for c in cases if c.classification == "완성 답안 요청"]
    assert answer_requests and all(c.response_mode is ResponseMode.HINT_ONLY for c in answer_requests)


def _llm_cases(cases):
    return [c for c in cases if c.response_mode in (ResponseMode.HINT_ONLY, ResponseMode.NEXT_STEP)]


def test_leaking_python_reply_is_blocked():
    cases = run(MockProvider(PY_FULL))
    assert _llm_cases(cases) and all(c.leak_blocked for c in _llm_cases(cases))
    assert all("bits = str(n % 2)" not in c.reply for c in cases)


@pytest.mark.xfail(strict=True, reason=(
    "누출 검사(thinkguard_nlp.leak, 규칙 기반)가 Python 문법만 본다 — 완성 C 함수가 그대로 통과. "
    "시연 과제가 C라서 NLP 쪽 수정 필요(11/25 졸라보기로 발견). 고치면 이 xfail을 지운다."
))
def test_leaking_c_reply_is_blocked():
    cases = run(MockProvider(C_FULL))
    assert _llm_cases(cases) and all(c.leak_blocked for c in _llm_cases(cases))


def test_prompt_has_fixed_rules_first_and_hidden_values_only_in_secret_block():
    llm = MockProvider()
    run(llm)
    assert llm.calls
    for system, messages in llm.calls:
        assert system.startswith(FIXED_RULES)
        before_secret = system.split(f"<{SECRET_TAG}>")[0]
        assert "SECRET-HIDDEN-OUT" not in before_secret
        if "[이 문항]\n변환기" in system:  # 코드 작성 문항 맥락이면 숨김 기대 출력은 비밀 블록에만 있다
            assert "SECRET-HIDDEN-OUT" in system
        assert all("SECRET" not in m.content for m in messages)  # 학생 쪽 메시지에는 없다


def test_no_ai_questions_means_no_cases():
    data = {**ASSIGNMENT, "questions": [{**q, "ai_help": False} for q in ASSIGNMENT["questions"]]}
    assert run(MockProvider(), data) == []


def test_simulate_api_needs_teacher_and_returns_cases(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    body = {**ASSIGNMENT, "class_id": klass["seq"]}
    res = client.post("/api/assignments/simulate", json=body, headers=teacher)
    assert res.status_code == 200, res.text
    cases = res.json()
    assert cases and {"question_index", "message", "classification", "attempt", "leak_blocked",
                      "external_signals", "reply", "response_mode"} <= set(cases[0])
    assert client.post("/api/assignments/simulate", json=body).status_code == 401
