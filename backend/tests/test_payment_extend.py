"""결제 목업 EXTEND — 내 클래스만, 1년 연장, 지금 학생 수보다 작은 요금제는 CONFLICT."""

from datetime import datetime

from fastapi.testclient import TestClient

from tests.factories import api_class, api_teacher


def extend(client, headers, class_id, plan="MEDIUM"):
    return client.post("/api/payments", json={"plan": plan, "kind": "EXTEND", "class_id": class_id}, headers=headers)


def test_extend_adds_one_year_and_changes_plan(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    res = extend(client, teacher, klass["seq"])
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["class_id"] == klass["seq"] and body["amount"] == 150_000 and body["student_limit"] == 100
    old, new = datetime.fromisoformat(klass["expires_at"]), datetime.fromisoformat(body["expires_at"])
    assert new.year == old.year + 1 and (new.month, new.day) == (old.month, old.day)
    after = client.get(f"/api/classes/{klass['seq']}", headers=teacher).json()
    assert after["plan"] == "MEDIUM" and after["student_limit"] == 100 and after["expires_at"] == body["expires_at"]


def test_extend_conflict_when_students_exceed_limit(client: TestClient, db, monkeypatch):
    from app.core.plans import PLANS, Plan

    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    client.put(f"/api/classes/{klass['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    for i in range(2):
        client.post("/api/enrollments", json={"invite_code": klass["invite_code"], "student_no": f"2026100{i}"})
    tiny = PLANS["SMALL"]
    monkeypatch.setitem(PLANS, "SMALL", Plan(**{**tiny.__dict__, "student_limit": 1}))
    res = extend(client, teacher, klass["seq"], "SMALL")
    assert res.status_code == 409 and res.json()["code"] == "CONFLICT"


def test_extend_other_teacher_class_is_forbidden_and_needs_class_id(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    other = api_teacher(client, email="other@example.test")
    assert extend(client, other, klass["seq"]).status_code == 403
    assert client.post("/api/payments", json={"plan": "SMALL", "kind": "EXTEND"}, headers=teacher).status_code == 400
    assert client.post("/api/payments", json={"plan": "SMALL", "kind": "NEW", "class_id": klass["seq"]},
                       headers=teacher).status_code == 400
