from app.classifier.base import ClassificationResult
from app.services.policy import ASK_ATTEMPT_REPLY, ResponseMode, decide


def result(**kw) -> ClassificationResult:
    base = dict(
        is_learning_context=True,
        requests_complete_answer=False,
        has_self_attempt_evidence=False,
        uncertain=False,
        confidence=0.9,
    )
    return ClassificationResult(**(base | kw))


def test_complete_answer_without_attempt_is_hint_only():
    d = decide(result(requests_complete_answer=True))
    assert d.mode is ResponseMode.HINT_ONLY
    assert d.fixed_reply is None
    assert "정답" in d.directive


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
