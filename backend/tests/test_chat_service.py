import asyncio

from app.classifier.base import ClassificationResult, Classifier
from app.leak_guard.base import LeakCheckResult, LeakGuard
from app.leak_guard.module import ModuleLeakGuard
from app.llm.mock import MockProvider
from app.schemas.chat import ChatTurn
from app.services import chat_service
from app.services.policy import ResponseMode
from app.services.prompt_builder import FIXED_RULES

GUARD = ModuleLeakGuard("thinkguard_nlp.leak:check_leak")


class FixedClassifier(Classifier):
    def __init__(self, **kw):
        base = dict(
            is_learning_context=True,
            requests_complete_answer=False,
            has_self_attempt_evidence=False,
            uncertain=False,
            confidence=0.9,
        )
        self._result = ClassificationResult(**(base | kw))

    async def classify(self, message, history):
        return self._result


def run(classifier, llm, message="정답 알려줘", history=None):
    return asyncio.run(
        chat_service.reply(message, history or [], "기본 프롬프트", classifier, llm, GUARD)
    )


def test_hint_only_calls_llm_with_fixed_rules_and_directive():
    llm = MockProvider()
    out = run(FixedClassifier(requests_complete_answer=True), llm)

    assert out.mode is ResponseMode.HINT_ONLY
    assert out.used_llm
    assert out.text == llm.reply
    system, messages = llm.calls[0]
    assert system.startswith("기본 프롬프트")
    assert FIXED_RULES in system
    assert "힌트만" in system
    assert messages[-1] == ChatTurn(role="student", content="정답 알려줘")


def test_history_is_passed_to_llm_before_new_message():
    llm = MockProvider()
    history = [ChatTurn(role="student", content="x=3 까지 했어요"), ChatTurn(role="assistant", content="좋아요")]
    run(FixedClassifier(has_self_attempt_evidence=True), llm, "다음은요?", history)
    _, messages = llm.calls[0]
    assert messages[:2] == history
    assert messages[2].content == "다음은요?"


def test_uncertain_skips_llm():
    llm = MockProvider()
    out = run(FixedClassifier(uncertain=True), llm)
    assert out.mode is ResponseMode.ASK_ATTEMPT
    assert not out.used_llm
    assert llm.calls == []


def test_empty_llm_reply_falls_back_to_fixed_message():
    from app.services.policy import ASK_ATTEMPT_REPLY

    llm = MockProvider(reply="   ")
    out = run(FixedClassifier(requests_complete_answer=True), llm)
    assert out.used_llm
    assert out.text == ASK_ATTEMPT_REPLY


class RecordingGuard(LeakGuard):
    def __init__(self):
        self.calls: list[tuple[str, list[ChatTurn]]] = []

    async def check(self, reply, history):
        self.calls.append((reply, list(history)))
        return LeakCheckResult(leaked=False)


def test_leak_guard_receives_current_student_message():
    """학생이 보낸 빈칸과 비교할 수 있도록 누출 검사에는 이번 학생 메시지까지 넘긴다."""
    guard = RecordingGuard()
    history = [ChatTurn(role="student", content="x=3 까지 했어요"), ChatTurn(role="assistant", content="좋아요")]
    classifier = FixedClassifier(has_self_attempt_evidence=True)
    asyncio.run(chat_service.reply("다음은요?", history, "", classifier, MockProvider(), guard))
    draft, checked = guard.calls[0]
    assert draft == MockProvider.DEFAULT_REPLY
    assert checked == [*history, ChatTurn(role="student", content="다음은요?")]
