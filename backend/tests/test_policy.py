import pytest

from app.classifier.base import ClassificationResult
from app.services.policy import ASK_ATTEMPT_REPLY, OFFER_CHOICES_REPLY, HelpChoice, ResponseMode, decide


def result(**kw) -> ClassificationResult:
    base = dict(
        is_learning_context=True,
        requests_complete_answer=False,
        has_self_attempt_evidence=False,
        uncertain=False,
        confidence=0.9,
    )
    return ClassificationResult(**(base | kw))


def test_complete_answer_without_attempt_offers_choices_without_llm():
    d = decide(result(requests_complete_answer=True))
    assert d.mode is ResponseMode.OFFER_CHOICES
    assert d.fixed_reply == OFFER_CHOICES_REPLY
    assert d.directive is None


@pytest.mark.parametrize("choice", list(HelpChoice))
def test_any_choice_stays_hint_only(choice):
    """I1: 무엇을 골라도(ORIGINAL 포함) 정책은 힌트만."""
    d = decide(result(requests_complete_answer=True), choice=choice)
    assert d.mode is ResponseMode.HINT_ONLY
    assert d.fixed_reply is None
    assert "정답" in d.directive and "힌트만" in d.directive


def test_choice_is_ignored_outside_answer_request():
    assert decide(result(), choice=HelpChoice.ORIGINAL).mode is ResponseMode.NEXT_STEP
    assert decide(result(uncertain=True), choice=HelpChoice.ORIGINAL).mode is ResponseMode.ASK_ATTEMPT


def test_modes_are_uppercase_strings():
    assert {m.value for m in ResponseMode} == {
        "NEXT_STEP", "HINT_ONLY", "ASK_ATTEMPT", "OFF_TOPIC", "USAGE_LIMIT", "OFFER_CHOICES",
    }


def test_complete_answer_with_attempt_gets_next_step():
    d = decide(result(requests_complete_answer=True, has_self_attempt_evidence=True))
    assert d.mode is ResponseMode.NEXT_STEP


def test_uncertain_asks_about_attempt_without_llm():
    d = decide(result(uncertain=True))
    assert d.mode is ResponseMode.ASK_ATTEMPT
    assert d.fixed_reply == ASK_ATTEMPT_REPLY
    assert d.directive is None


def test_low_confidence_is_treated_as_uncertain():
    assert decide(result(confidence=0.4), min_confidence=0.5).mode is ResponseMode.ASK_ATTEMPT
    assert decide(result(confidence=0.5), min_confidence=0.5).mode is ResponseMode.NEXT_STEP


def test_uncertain_wins_over_answer_request():
    d = decide(result(requests_complete_answer=True, uncertain=True))
    assert d.mode is ResponseMode.ASK_ATTEMPT


def test_off_topic_redirects_without_llm():
    d = decide(result(is_learning_context=False))
    assert d.mode is ResponseMode.OFF_TOPIC
    assert d.fixed_reply
