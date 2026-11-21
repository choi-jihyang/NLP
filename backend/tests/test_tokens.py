from datetime import timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.core.clock import now_kst
from app.core.config import Settings
from app.core.enums import Role
from app.core.errors import AppError, ErrorCode
from app.core.tokens import TokenClaims, decode_token, issue_token
from app.models import User
from tests.conftest import TEST_JWT_SECRET


def _user(seq: int = 7, role: Role = Role.TEACHER) -> User:
    return User(seq=seq, role=role, name="교수")


def _payload(**overrides: object) -> dict[str, object]:
    now = int(now_kst().timestamp())
    base: dict[str, object] = {"sub": "7", "role": "TEACHER", "iat": now, "exp": now + 3600}
    return {**base, **overrides}


def _assert_unauthorized(token: str) -> None:
    with pytest.raises(AppError) as info:
        decode_token(token)
    assert info.value.code == ErrorCode.UNAUTHORIZED


def test_issue_and_decode_roundtrip():
    token = issue_token(_user(), now_kst() + timedelta(hours=12))
    assert decode_token(token) == TokenClaims(user_seq=7, role=Role.TEACHER)
    raw = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
    assert raw["sub"] == "7" and raw["role"] == "TEACHER"
    assert raw["exp"] - raw["iat"] == 12 * 3600


def test_naive_expiry_rejected():
    with pytest.raises(ValueError, match="시간대"):
        issue_token(_user(), now_kst().replace(tzinfo=None))


def test_expired_token_rejected():
    _assert_unauthorized(issue_token(_user(), now_kst() - timedelta(seconds=1)))


def test_other_key_rejected():
    _assert_unauthorized(jwt.encode(_payload(), "another-secret-0123456789abcdef0123", algorithm="HS256"))


def test_unsigned_token_rejected():
    _assert_unauthorized(jwt.encode(_payload(), "", algorithm="none"))


def test_garbage_rejected():
    _assert_unauthorized("not-a-token")


def test_non_numeric_sub_rejected():
    _assert_unauthorized(jwt.encode(_payload(sub="abc"), TEST_JWT_SECRET, algorithm="HS256"))


def test_unknown_role_rejected():
    _assert_unauthorized(jwt.encode(_payload(role="ADMIN"), TEST_JWT_SECRET, algorithm="HS256"))


def test_missing_claim_rejected():
    payload = _payload()
    del payload["role"]
    _assert_unauthorized(jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256"))


def test_short_secret_rejected():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(jwt_secret="short", _env_file=None)


def test_missing_secret_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None)


def test_teacher_token_hours_default():
    assert Settings(jwt_secret=TEST_JWT_SECRET, _env_file=None).teacher_token_hours == 12


def test_short_secret_not_echoed():
    with pytest.raises(ValidationError) as info:
        Settings(jwt_secret="too-short-secret-value", _env_file=None)
    assert "too-short-secret-value" not in str(info.value)


def test_bad_secret_exits_with_one_line_message(monkeypatch: pytest.MonkeyPatch):
    from app.core.config import load_settings

    monkeypatch.setenv("JWT_SECRET", "too-short-secret-value")
    with pytest.raises(SystemExit) as info:
        load_settings(_env_file=None)
    message = str(info.value)
    assert "JWT_SECRET은 32자 이상" in message
    assert "too-short-secret-value" not in message
    assert "\n" not in message
