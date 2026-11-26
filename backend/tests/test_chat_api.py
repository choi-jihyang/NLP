"""⑥ 채팅 API · 붙여넣기 — I1(고르기 후 HINT_ONLY) · I5(내용 없음) · I6(상한이면 LLM 없음) · I7 · 잠김."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.classifier.base import ClassificationResult, Classifier
from app.llm.mock import MockProvider
from app.models import ChatMessage, PasteEvent
from app.services.policy import OFFER_CHOICES_REPLY, USAGE_LIMIT_REPLY
from app.services.prompt_builder import FIXED_RULES, SECRET_TAG
from tests.factories import api_class, api_teacher, bearer
from tests.test_submissions import ASSIGNMENT, setup, submit

PY_FULL = (
    "```python\ndef to_binary(n):\n    if n == 0:\n        return '0'\n    bits = ''\n    while n > 0:\n"
    "        bits = str(n % 2) + bits\n        n //= 2\n    return bits\n```"
)


class SpyClassifier(Classifier):
    def __init__(self, **kw):
        base = dict(is_learning_context=True, requests_complete_answer=False, has_self_attempt_evidence=False,
                    uncertain=False, confidence=0.9)
        self.result = ClassificationResult(**(base | kw))
        self.seen: list[str] = []

    async def classify(self, message, history):
        self.seen.append(message)
        return self.result


@pytest.fixture
def ai(monkeypatch):
    class Box:
        classifier = SpyClassifier()
        llm = MockProvider()

    monkeypatch.setattr("app.api.routes.chat.get_classifier", lambda: Box.classifier)
    monkeypatch.setattr("app.api.routes.chat.get_llm_provider", lambda: Box.llm)
    return Box


def chat_url(aid, qid):
    return f"/api/assignments/{aid}/questions/{qid}/chat"


def send(client, student, aid, qid, message="", choice=None):
    body = {"message": message} | ({"choice": choice} if choice else {})
    return client.post(chat_url(aid, qid), json=body, headers=student)


def test_empty_chat_state(client: TestClient, ai):
    _, student, aid, qids = setup(client)
    res = client.get(chat_url(aid, qids[2]), headers=student)
    assert res.status_code == 200
    assert res.json() == {"question_id": qids[2], "turns": [], "hint_step": 0, "max_hint_steps": 3,
                          "usage_remaining": 30}


def test_answer_request_offers_choices_then_hint_only(client: TestClient, ai):
    """I1: 고르기 전에는 LLM 없이 OFFER_CHOICES, 고른 뒤(ORIGINAL 포함)는 HINT_ONLY."""
    ai.classifier = SpyClassifier(requests_complete_answer=True)
    _, student, aid, qids = setup(client)
    first = send(client, student, aid, qids[2], "코드 전체 짜주세요").json()
    assert [t["response_mode"] for t in first["turns"]] == [None, "OFFER_CHOICES"]
    assert first["turns"][1]["text"] == OFFER_CHOICES_REPLY and ai.llm.calls == []
    picked = send(client, student, aid, qids[2], choice="ORIGINAL").json()
    assert picked["turns"][-1]["response_mode"] == "HINT_ONLY"
    assert picked["turns"][-2]["text"] == "원래 질문 그대로 보내기"  # 빈 말풍선 대신 고른 방식
    assert ai.classifier.seen[-1] == "코드 전체 짜주세요"  # 빈 메시지가 아니라 원래 요청을 분류
    assert picked["hint_step"] == 1 and picked["usage_remaining"] == 28
    system, messages = ai.llm.calls[0]
    assert system.startswith(FIXED_RULES)
    assert "11111111" in system.split(f"<{SECRET_TAG}>")[1]  # 숨김 기대 출력은 비밀 블록에만
    assert "11111111" not in system.split(f"<{SECRET_TAG}>")[0]
    assert messages[-1].content == "코드 전체 짜주세요"


def test_choice_without_offer_is_conflict(client: TestClient, ai):
    _, student, aid, qids = setup(client)
    assert send(client, student, aid, qids[2], choice="FIRST_HINT").status_code == 409
    assert send(client, student, aid, qids[2], "").status_code == 400


def test_uncertain_asks_attempt_without_llm(client: TestClient, ai):
    ai.classifier = SpyClassifier(uncertain=True)
    _, student, aid, qids = setup(client)
    state = send(client, student, aid, qids[2], "음").json()
    assert state["turns"][-1]["response_mode"] == "ASK_ATTEMPT" and ai.llm.calls == []
    assert state["hint_step"] == 0


def test_next_step_increments_hint_until_max(client: TestClient, ai):
    ai.classifier = SpyClassifier(has_self_attempt_evidence=True)
    _, student, aid, qids = setup(client)
    for _ in range(4):
        state = send(client, student, aid, qids[2], "while 문까지 썼어요").json()
    assert state["hint_step"] == 3  # STEP · EARNED 최대 3


def test_leaked_reply_is_replaced_and_draft_stored_privately(client: TestClient, db, ai):
    ai.classifier = SpyClassifier(has_self_attempt_evidence=True)
    ai.llm = MockProvider(PY_FULL)
    _, student, aid, qids = setup(client)
    res = send(client, student, aid, qids[2], "어떻게 해요")
    assert "bits = str" not in res.text and "blocked_draft" not in res.text
    msg = db.scalar(select(ChatMessage).where(ChatMessage.role == "ASSISTANT"))
    assert msg.leak_blocked is True and "bits = str" in msg.blocked_draft
    assert res.json()["hint_step"] == 0  # 막힌 답은 힌트 단계를 올리지 않는다


def test_classification_is_stored_but_not_returned(client: TestClient, db, ai):
    _, student, aid, qids = setup(client)
    res = send(client, student, aid, qids[2], "힌트 주세요")
    assert "confidence" not in res.text and "is_learning_context" not in res.text
    msg = db.scalar(select(ChatMessage).where(ChatMessage.role == "STUDENT"))
    assert msg.confidence == 0.9 and msg.is_learning_context is True


def test_demo_trace_only_when_enabled(client: TestClient, ai, monkeypatch):
    from app.core.config import get_settings

    _, student, aid, qids = setup(client)
    assert send(client, student, aid, qids[2], "힌트").json()["turns"][-1]["trace"] is None
    monkeypatch.setattr(get_settings(), "demo_trace", True)
    trace = send(client, student, aid, qids[2], "힌트").json()["turns"][-1]["trace"]
    assert trace["classification"] == "학습 질문" and trace["leak_blocked"] is False


def test_usage_limit_stops_llm_and_classifier(client: TestClient, ai):
    """I6: 상한이면 분류기 · LLM을 부르지 않는다. 사용량은 과제 전체(모든 문항) 학생 메시지 수."""
    _, student, aid, qids = setup(client, policy={"usage_limit": 2})
    send(client, student, aid, qids[2], "힌트 1")
    send(client, student, aid, qids[1], "힌트 2")  # 다른 문항도 함께 센다
    calls, seen = len(ai.llm.calls), len(ai.classifier.seen)
    state = send(client, student, aid, qids[2], "힌트 3").json()
    assert state["turns"][-1]["response_mode"] == "USAGE_LIMIT" and state["turns"][-1]["text"] == USAGE_LIMIT_REPLY
    assert len(ai.llm.calls) == calls and len(ai.classifier.seen) == seen
    assert state["usage_remaining"] == 0


def test_locked_during_concept_check_after_finalize_and_ai_off_project(client: TestClient, ai):
    _, student, aid, qids = setup(client)
    submit(client, student, aid, qids[0], "0")  # 힌트 없이 처음 → AWAITING_CHECK
    assert send(client, student, aid, qids[0], "힌트").status_code == 403

    data = {**ASSIGNMENT, "questions": [{**ASSIGNMENT["questions"][3], "ai_help": False}],
            "policy": {"concept_check_enabled": False}}
    teacher = api_teacher(client, email="t2@example.test")
    klass = api_class(client, teacher, name="2분반")
    aid2 = client.post(f"/api/classes/{klass['seq']}/assignments", json=data, headers=teacher).json()["seq"]
    client.post(f"/api/assignments/{aid2}/publish", headers=teacher)
    client.put(f"/api/classes/{klass['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    s2 = bearer(client.post("/api/enrollments", json={"invite_code": klass["invite_code"],
                                                      "student_no": "20269999"}).json()["access_token"])
    q2 = client.get(f"/api/assignments/{aid2}", headers=teacher).json()["questions"][0]["seq"]
    assert send(client, s2, aid2, q2, "힌트").status_code == 403
    submit(client, s2, aid2, q2, "int main(){}")
    client.post(f"/api/assignments/{aid2}/submission/finalize", headers=s2)
    assert send(client, s2, aid2, q2, "힌트").json()["code"] == "ALREADY_SUBMITTED"


def test_pasted_field_is_rejected_in_chat(client: TestClient, ai):
    _, student, aid, qids = setup(client)
    res = client.post(chat_url(aid, qids[2]), json={"message": "x", "pasted": True}, headers=student)
    assert res.status_code == 400


def test_other_student_cannot_read_chat(client: TestClient, ai):
    teacher, student, aid, qids = setup(client)
    send(client, student, aid, qids[2], "내 비밀 질문")
    klass_id = client.get(f"/api/assignments/{aid}", headers=teacher).json()["class_id"]
    invite = client.get(f"/api/classes/{klass_id}", headers=teacher).json()["invite_code"]
    other = bearer(client.post("/api/enrollments", json={"invite_code": invite, "student_no": "20260002"})
                   .json()["access_token"])
    res = client.get(chat_url(aid, qids[2]), headers=other)
    assert res.status_code == 200 and "내 비밀 질문" not in res.text  # 같은 반이어도 자기 대화만
    assert client.get(chat_url(aid, qids[2]), headers=teacher).status_code == 403


# ---- 붙여넣기 (I5) ----


def test_paste_event_stores_length_and_time_only(client: TestClient, db, ai):
    _, student, aid, qids = setup(client)
    body = {"question_id": qids[2], "field": "ANSWER", "length": 312, "pasted_at": "2026-11-25T23:00:00+09:00"}
    assert client.post("/api/paste-events", json=body, headers=student).json() == {"ok": True}
    event = db.scalar(select(PasteEvent))
    assert (event.field, event.length) == ("ANSWER", 312)
    assert event.pasted_at == datetime.fromisoformat("2026-11-25T23:00:00+09:00")
    assert {c.name for c in PasteEvent.__table__.columns} == {"seq", "answer_id", "field", "length", "pasted_at",
                                                               "created_at"}


def test_paste_event_rejects_content_and_other_classes(client: TestClient, ai):
    _, student, aid, qids = setup(client)
    base = {"question_id": qids[2], "field": "CHAT", "length": 5, "pasted_at": "2026-11-25T23:00:00+09:00"}
    assert client.post("/api/paste-events", json=base | {"content": "secret"}, headers=student).status_code == 400
    assert client.post("/api/paste-events", json=base | {"question_id": 99999}, headers=student).status_code == 404
    other_teacher = api_teacher(client, email="x@example.test")
    k = api_class(client, other_teacher, name="3분반")
    client.put(f"/api/classes/{k['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=other_teacher)
    outsider = bearer(client.post("/api/enrollments", json={"invite_code": k["invite_code"],
                                                            "student_no": "1"}).json()["access_token"])
    assert client.post("/api/paste-events", json=base, headers=outsider).status_code == 403
