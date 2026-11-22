from fastapi.testclient import TestClient

from tests.factories import api_class, api_teacher, bearer


def _join(client: TestClient, code: object, student_no: str, headers: dict[str, str] | None = None) -> dict:
    res = client.post("/api/enrollments", json={"invite_code": code, "student_no": student_no}, headers=headers or {})
    assert res.status_code == 200, res.text
    return res.json()


def test_demo_flow_class_to_my_classes(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid, code = klass["seq"], klass["invite_code"]
    roster = {"join_mode": "APPROVAL", "roster": [{"student_no": "20260001", "is_use": True}]}
    assert client.put(f"/api/classes/{cid}/roster", json=roster, headers=teacher).status_code == 200

    listed = _join(client, code, "20260001")
    assert (listed["class_id"], listed["status"]) == (cid, "APPROVED")

    waiting = _join(client, code, "20260099")
    student = bearer(waiting["access_token"])
    assert waiting["status"] == "PENDING"
    assert client.get(f"/api/enrollments/{cid}/me", headers=student).json() == {"status": "PENDING"}
    assert client.post(f"/api/enrollments/{cid}/consent", headers=student).status_code == 403

    requests = client.get(f"/api/classes/{cid}/join-requests", headers=teacher).json()
    assert [(r["student_no"], r["is_reentry"]) for r in requests] == [("20260099", False)]
    path = f"/api/classes/{cid}/join-requests/{requests[0]['seq']}"
    decided = client.post(path, json={"approve": True}, headers=teacher)
    assert decided.json() == {"status": "APPROVED"}

    assert client.post(f"/api/enrollments/{cid}/consent", headers=student).json() == {"ok": True}
    mine = client.get("/api/me/classes", headers=student).json()
    assert mine == [{
        "class_id": cid, "class_name": "1분반", "student_no": "20260099",
        "enrollment_status": "APPROVED", "assignments": [],
    }]

    students = client.get(f"/api/classes/{cid}/students", headers=teacher).json()
    assert [s["student_no"] for s in students] == ["20260001", "20260099"]
    assert all(isinstance(s["seq"], int) for s in students)
    assert client.get(f"/api/classes/{cid}", headers=teacher).json()["student_count"] == 2


def _roster(client: TestClient, cid: object, teacher: dict[str, str], *numbers: str, mode: str = "APPROVAL") -> None:
    body = {"join_mode": mode, "roster": [{"student_no": n} for n in numbers]}
    assert client.put(f"/api/classes/{cid}/roster", json=body, headers=teacher).status_code == 200


def test_reentry_gives_ticket_and_reject_keeps_impostor_out(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid = klass["seq"]
    _roster(client, cid, teacher, "A")
    original = bearer(_join(client, klass["invite_code"], "A")["access_token"])

    impostor = _join(client, klass["invite_code"], "A")  # 토큰 없이 같은 학번
    assert impostor["status"] == "PENDING" and impostor["access_token"] is None and impostor["reentry_ticket"]
    claim = client.post("/api/enrollments/reentry", json={"ticket": impostor["reentry_ticket"]})
    assert claim.json() == {"status": "PENDING", "access_token": None}
    assert client.post(f"/api/enrollments/{cid}/consent", headers=original).status_code == 200  # 원래 기기는 그대로

    request = client.get(f"/api/classes/{cid}/join-requests", headers=teacher).json()[0]
    assert request["is_reentry"] is True
    client.post(f"/api/classes/{cid}/join-requests/{request['seq']}", json={"approve": False}, headers=teacher)
    after = client.post("/api/enrollments/reentry", json={"ticket": impostor["reentry_ticket"]})
    assert after.status_code == 404  # 거절하면 티켓이 무효(리뷰 C1)


def test_approved_reentry_gets_token_once(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid = klass["seq"]
    _roster(client, cid, teacher, "A")
    _join(client, klass["invite_code"], "A")
    ticket = _join(client, klass["invite_code"], "A")["reentry_ticket"]
    request = client.get(f"/api/classes/{cid}/join-requests", headers=teacher).json()[0]
    client.post(f"/api/classes/{cid}/join-requests/{request['seq']}", json={"approve": True}, headers=teacher)
    claimed = client.post("/api/enrollments/reentry", json={"ticket": ticket}).json()
    assert claimed["status"] == "APPROVED" and claimed["access_token"]
    assert client.post(f"/api/enrollments/{cid}/consent", headers=bearer(claimed["access_token"])).status_code == 200
    assert client.post("/api/enrollments/reentry", json={"ticket": ticket}).status_code == 404


def test_reentry_does_not_expose_other_classes(client: TestClient):
    teacher = api_teacher(client)
    class_a, class_b = api_class(client, teacher, "A반"), api_class(client, teacher, "B반")
    _roster(client, class_a["seq"], teacher, "S1")
    _roster(client, class_b["seq"], teacher, "S1")
    victim = bearer(_join(client, class_a["invite_code"], "S1")["access_token"])
    _join(client, class_b["invite_code"], "S1", victim)  # 같은 계정으로 B 참여
    impostor = _join(client, class_a["invite_code"], "S1")  # A 코드 + 학번만 앎
    assert impostor["access_token"] is None  # 리뷰 C2: B를 볼 토큰이 없다


def test_reentry_does_not_free_a_seat(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid, code = klass["seq"], klass["invite_code"]
    client.put(f"/api/classes/{cid}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    for n in range(50):
        _join(client, code, f"S{n}")
    _join(client, code, "S0")  # 다시 입장 요청
    full = client.post("/api/enrollments", json={"invite_code": code, "student_no": "X"})
    assert full.status_code == 409 and full.json()["code"] == "CLASS_FULL"  # 리뷰 I1


def test_deleted_account_token_is_treated_as_no_token(client: TestClient, db):  # noqa: ANN001
    from app.models import User

    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    client.put(f"/api/classes/{klass['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    token = _join(client, klass["invite_code"], "A")["access_token"]
    ghost = User(role="STUDENT", name="ghost")
    db.add(ghost)
    db.commit()
    from datetime import timedelta

    from app.core.clock import now_kst
    from app.core.tokens import issue_token

    ghost_token = issue_token(ghost, now_kst() + timedelta(hours=1))
    db.delete(ghost)
    db.commit()
    res = _join(client, klass["invite_code"], "B", bearer(ghost_token))
    assert res["status"] == "APPROVED" and res["access_token"] != token


def test_join_errors_and_validation(client: TestClient):
    assert client.post("/api/enrollments", json={"invite_code": "TG-0000", "student_no": "1"}).status_code == 404
    bad = client.post("/api/enrollments", json={"invite_code": "TG-0000", "student_no": "20 26"})
    assert bad.status_code == 400 and bad.json()["code"] == "VALIDATION_FAILED"


def test_removed_student_loses_access(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid = klass["seq"]
    client.put(f"/api/classes/{cid}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    joined = _join(client, klass["invite_code"], "A")
    student = bearer(joined["access_token"])
    student_seq = client.get(f"/api/classes/{cid}/students", headers=teacher).json()[0]["seq"]
    assert client.delete(f"/api/classes/{cid}/students/{student_seq}", headers=teacher).json() == {"ok": True}
    assert client.post(f"/api/enrollments/{cid}/consent", headers=student).status_code == 403
    body = {"invite_code": klass["invite_code"], "student_no": "A"}
    again = client.post("/api/enrollments", json=body, headers=student)
    assert again.status_code == 403


def test_student_endpoints_need_student_token(client: TestClient):
    teacher = api_teacher(client)
    assert client.get("/api/me/classes", headers=teacher).status_code == 403
    assert client.get("/api/me/classes").status_code == 401
