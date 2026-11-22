from fastapi.testclient import TestClient

from app.api.errors import REQUEST_ID_HEADER
from app.core.tokens import decode_token

SIGNUP = {"name": "김교수", "email": "Teacher@Example.test", "password": "correct-horse"}


def test_signup_returns_201_with_token_and_user(client: TestClient):
    res = client.post("/api/auth/signup", json=SIGNUP)
    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"access_token", "user"}
    user = body["user"]
    assert set(user) == {"seq", "name", "email", "role"}
    assert isinstance(user["seq"], int)
    assert (user["name"], user["email"], user["role"]) == ("김교수", "teacher@example.test", "TEACHER")
    assert decode_token(body["access_token"]).user_seq == user["seq"]


def test_signup_duplicate_is_409(client: TestClient):
    client.post("/api/auth/signup", json=SIGNUP)
    res = client.post("/api/auth/signup", json={**SIGNUP, "email": "teacher@example.test"})
    assert res.status_code == 409
    assert res.json()["code"] == "EMAIL_TAKEN"


def test_signup_short_password_is_400(client: TestClient):
    res = client.post("/api/auth/signup", json={**SIGNUP, "password": "1234567"})
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert "password" in body["message"]
    assert body["trace_id"] == res.headers[REQUEST_ID_HEADER]


def test_signup_long_password_is_400(client: TestClient):
    assert client.post("/api/auth/signup", json={**SIGNUP, "password": "p" * 129}).status_code == 400


def test_signup_lone_surrogate_password_is_400(client: TestClient):
    raw = '{"name": "김교수", "email": "t@example.test", "password": "abcdefgh\\ud800"}'
    res = client.post("/api/auth/signup", content=raw.encode(), headers={"Content-Type": "application/json"})
    assert res.status_code == 400


def test_login_success_and_failure(client: TestClient):
    client.post("/api/auth/signup", json=SIGNUP)
    ok = client.post("/api/auth/login", json={"email": "TEACHER@example.test", "password": "correct-horse"})
    assert ok.status_code == 200
    assert ok.json()["user"]["email"] == "teacher@example.test"
    bad = client.post("/api/auth/login", json={"email": "teacher@example.test", "password": "nope-nope"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "INVALID_CREDENTIALS"
    assert bad.json()["message"] == "이메일 또는 비밀번호가 올바르지 않습니다."
