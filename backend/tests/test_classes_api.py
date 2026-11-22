from fastapi.testclient import TestClient

from tests.factories import api_class, api_teacher, bearer


def test_plans_are_public(client: TestClient):
    res = client.get("/api/plans")
    assert res.status_code == 200
    assert res.json()[0] == {"code": "SMALL", "name": "Small", "student_limit": 50, "price": 90_000}


def test_payment_and_class_creation(client: TestClient):
    teacher = api_teacher(client)
    pay = client.post("/api/payments", json={"plan": "MEDIUM", "kind": "NEW"}, headers=teacher)
    assert pay.status_code == 201
    body = pay.json()
    assert body == {"payment_seq": body["payment_seq"], "plan": "MEDIUM", "student_limit": 100, "amount": 150_000}
    created = api_class(client, teacher)
    fields = {"seq", "name", "invite_code", "plan", "student_limit", "student_count", "starts_at", "expires_at"}
    assert set(created) == fields
    assert created["student_count"] == 0 and str(created["starts_at"]).endswith("+09:00")
    listed = client.get("/api/classes", headers=teacher).json()
    assert [c["seq"] for c in listed] == [created["seq"]]


def test_extend_payment_is_rejected(client: TestClient):
    teacher = api_teacher(client)
    res = client.post("/api/payments", json={"plan": "SMALL", "kind": "EXTEND"}, headers=teacher)
    assert res.status_code == 400


def test_blank_class_name_is_rejected(client: TestClient):
    teacher = api_teacher(client)
    pay = client.post("/api/payments", json={"plan": "SMALL", "kind": "NEW"}, headers=teacher).json()
    body = {"name": "  ", "starts_on": "2099-01-01", "payment_seq": pay["payment_seq"]}
    res = client.post("/api/classes", json=body, headers=teacher)
    assert res.status_code == 400


def test_other_teacher_gets_403(client: TestClient):
    owner = api_teacher(client, "a@example.test")
    other = api_teacher(client, "b@example.test")
    seq = api_class(client, owner)["seq"]
    for path in (f"/api/classes/{seq}", f"/api/classes/{seq}/roster", f"/api/classes/{seq}/students"):
        assert client.get(path, headers=other).status_code == 403
    assert client.get("/api/classes/999", headers=owner).status_code == 404


def test_teacher_api_needs_teacher_token(client: TestClient):
    owner = api_teacher(client)
    klass = api_class(client, owner)
    joined = client.post("/api/enrollments", json={"invite_code": klass["invite_code"], "student_no": "1"}).json()
    assert client.get("/api/classes", headers=bearer(joined["access_token"])).status_code == 403
    assert client.get("/api/classes").status_code == 401


def test_ai_defaults_roundtrip(client: TestClient):
    teacher = api_teacher(client)
    seq = api_class(client, teacher)["seq"]
    policy = client.get(f"/api/classes/{seq}/ai-defaults", headers=teacher).json()
    policy.update(usage_limit=5, prompt_mode="CUSTOM", custom_prompt="x")
    saved = client.put(f"/api/classes/{seq}/ai-defaults", json=policy, headers=teacher).json()
    assert (saved["usage_limit"], saved["prompt_mode"], saved["custom_prompt"]) == (5, "FORM", None)


def test_roster_roundtrip(client: TestClient):
    teacher = api_teacher(client)
    seq = api_class(client, teacher)["seq"]
    body = {"join_mode": "OPEN", "roster": [{"student_no": " 20260001 ", "is_use": True}, {"student_no": "20260002"}]}
    saved = client.put(f"/api/classes/{seq}/roster", json=body, headers=teacher)
    assert saved.status_code == 200
    assert saved.json() == {
        "join_mode": "OPEN",
        "roster": [{"student_no": "20260001", "is_use": True}, {"student_no": "20260002", "is_use": True}],
    }
