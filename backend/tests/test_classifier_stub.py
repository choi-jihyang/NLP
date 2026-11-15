import asyncio

import pytest

from app.classifier.keyword_stub import KeywordStubClassifier
from app.schemas.chat import ChatTurn


def classify(message: str, history: list[ChatTurn] | None = None):
    return asyncio.run(KeywordStubClassifier().classify(message, history or []))


@pytest.mark.parametrize("msg", ["정답만 빨리 알려주세요", "이거 풀어줘", "전체 코드 짜줘", "그냥 알려줘요"])
def test_answer_request_without_attempt(msg):
    r = classify(msg)
    assert r.requests_complete_answer
    assert not r.has_self_attempt_evidence
    assert not r.uncertain


@pytest.mark.parametrize(
    "msg",
    ["2로 나눠서 x²−4x+3=0 까지 했어요", "근을 구해보니 2랑 3이 나왔어요", "for i in range(n): 까지 짜봤어요"],
)
def test_attempt_evidence(msg):
    assert classify(msg).has_self_attempt_evidence


def test_attempt_in_earlier_student_turn_counts():
    history = [ChatTurn(role="student", content="D=b²−4ac 에 넣어서 16−4k 까지 했어요")]
    r = classify("이제 정답 알려줘", history)
    assert r.requests_complete_answer
    assert r.has_self_attempt_evidence


def test_attempt_only_in_assistant_turn_does_not_count():
    history = [ChatTurn(role="assistant", content="x = 3 이 되도록 정리해 보세요")]
    assert not classify("정답 알려줘", history).has_self_attempt_evidence


def test_unmatched_message_is_uncertain():
    r = classify("음")
    assert r.uncertain
    assert r.confidence < 0.5


def test_off_topic():
    assert not classify("오늘 날씨 어때?").is_learning_context
