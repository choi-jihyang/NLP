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


def test_reentry_token_is_blocked_until_approved(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    cid = klass["seq"]
    roster = {"join_mode": "APPROVAL", "roster": [{"student_no": "A"}]}
    client.put(f"/api/classes/{cid}/roster", json=roster, headers=teacher)
    original = bearer(_join(client, klass["invite_code"], "A")["access_token"])
    assert client.post(f"/api/enrollments/{cid}/consent", headers=original).status_code == 200

    impostor = _join(client, klass["invite_code"], "A")  # 토큰 없이 같은 학번
    assert impostor["status"] == "PENDING"
    assert client.post(f"/api/enrollments/{cid}/consent", headers=bearer(impostor["access_token"])).status_code == 403

    request = client.get(f"/api/classes/{cid}/join-requests", headers=teacher).json()[0]
    assert request["is_reentry"] is True
    client.post(f"/api/classes/{cid}/join-requests/{request['seq']}", json={"approve": False}, headers=teacher)
    assert client.post(f"/api/enrollments/{cid}/consent", headers=original).status_code == 200


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
