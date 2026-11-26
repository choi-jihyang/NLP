import asyncio

from app.classifier.base import ClassificationResult, Classifier
from app.leak_guard.module import ModuleLeakGuard
from app.llm.mock import MockProvider
from app.schemas.chat import ChatTurn
from app.services import chat_service
from app.services.policy import HelpChoice, ResponseMode
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


def run(classifier, llm, message="정답 알려줘", history=None, choice=None, context=None):
    return asyncio.run(
        chat_service.reply(message, history or [], "기본 프롬프트", classifier, llm, GUARD,
                           choice=choice, context=context)
    )


def test_hint_only_calls_llm_with_fixed_rules_and_directive():
    llm = MockProvider()
    out = run(FixedClassifier(requests_complete_answer=True), llm, choice=HelpChoice.FIRST_HINT)

    assert out.mode is ResponseMode.HINT_ONLY
    assert out.used_llm
    assert out.text == llm.reply
    system, messages = llm.calls[0]
    assert system.startswith(FIXED_RULES)
    assert "기본 프롬프트" in system
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
    out = run(FixedClassifier(requests_complete_answer=True), llm, choice=HelpChoice.FIRST_HINT)
    assert out.used_llm
    assert out.text == ASK_ATTEMPT_REPLY


def test_complete_answer_without_choice_offers_choices_without_llm():
    from app.services.policy import OFFER_CHOICES_REPLY

    llm = MockProvider()
    out = run(FixedClassifier(requests_complete_answer=True), llm)
    assert out.mode is ResponseMode.OFFER_CHOICES
    assert out.text == OFFER_CHOICES_REPLY
    assert not out.used_llm
    assert llm.calls == []


def test_context_builds_system_prompt_from_policy():
    from app.schemas.ai_policy import AiPolicy
    from app.services.prompt_builder import PromptContext

    llm = MockProvider()
    ctx = PromptContext(policy=AiPolicy(), description="2진수 변환기", protected_values=["1010"])
    run(FixedClassifier(has_self_attempt_evidence=True), llm, context=ctx)
    system, _ = llm.calls[0]
    assert system.startswith(FIXED_RULES)
    assert "기본 프롬프트" not in system
    assert "<과제 설명>" in system and "1010" in system
