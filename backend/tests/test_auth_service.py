from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import KST, now_kst
from app.core.enums import Role
from app.core.errors import AppError, ErrorCode
from app.core.security import verify_password
from app.core.tokens import decode_token
from app.models import User
from app.schemas.auth import SignupRequest
from app.services import auth_service
from app.services.auth_service import login, signup


def _signup(db: Session, email: str = "teacher@example.test") -> User:
    return signup(db, "김교수", email, "correct-horse").user


def test_signup_creates_teacher(db: Session):
    result = signup(db, "김교수", "  Teacher@Example.TEST ", "correct-horse")
    user = result.user
    assert user.seq is not None and user.role == Role.TEACHER
    assert user.email == "teacher@example.test"
    assert user.password_hash and verify_password("correct-horse", user.password_hash)
    assert user.login_at is not None and user.login_at.tzinfo is not None
    claims = decode_token(result.access_token)
    assert (claims.user_seq, claims.role) == (user.seq, Role.TEACHER)


def test_duplicate_email_case_insensitive(db: Session):
    _signup(db, "teacher@x.test")
    with pytest.raises(AppError) as info:
        signup(db, "다른 교수", "Teacher@X.test", "another-pass")
    assert info.value.code == ErrorCode.EMAIL_TAKEN
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_login_updates_login_at(db: Session):
    user = _signup(db)
    old = datetime(2026, 1, 1, tzinfo=KST)
    user.login_at = old
    db.commit()
    result = login(db, " TEACHER@example.test", "correct-horse")
    assert result.user.seq == user.seq
    assert result.user.login_at is not None and result.user.login_at > old


@pytest.mark.parametrize("email,password", [
    ("teacher@example.test", "wrong-password"),
    ("nobody@example.test", "correct-horse"),
])
def test_login_failures_look_the_same(db: Session, email: str, password: str):
    _signup(db)
    with pytest.raises(AppError) as info:
        login(db, email, password)
    assert info.value.code == ErrorCode.INVALID_CREDENTIALS
    assert info.value.message == "이메일 또는 비밀번호가 올바르지 않습니다."


def test_student_account_cannot_password_login(db: Session):
    db.add(User(role=Role.STUDENT, name="20260001", email="s@example.test"))  # 비밀번호 없음
    db.commit()
    with pytest.raises(AppError) as info:
        login(db, "s@example.test", "")
    assert info.value.code == ErrorCode.INVALID_CREDENTIALS


def test_unknown_email_still_runs_password_check(db: Session, monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []
    real = auth_service.verify_password
    monkeypatch.setattr(auth_service, "verify_password", lambda pw, stored: calls.append(pw) or real(pw, stored))
    with pytest.raises(AppError):
        login(db, "nobody@example.test", "anything")
    assert calls == ["anything"]  # 계정이 없어도 해시 계산을 한 번 한다(응답 시간 차이 줄이기)


def test_teacher_token_lasts_configured_hours(db: Session):
    before = now_kst()
    result = signup(db, "김교수", "t2@example.test", "correct-horse")
    import jwt

    from tests.conftest import TEST_JWT_SECRET

    raw = jwt.decode(result.access_token, TEST_JWT_SECRET, algorithms=["HS256"])
    assert abs(raw["exp"] - (before + timedelta(hours=12)).timestamp()) < 5


@pytest.mark.parametrize("field,value", [
    ("name", "   "),
    ("name", "가" * 101),
    ("email", "no-at-sign"),
    ("email", "a@b"),
    ("email", "x" * 250 + "@b.test"),
    ("password", "short7!"),
    ("password", "p" * 129),
    ("password", "abcdefgh\ud800"),
])
def test_signup_request_rejects(field: str, value: str):
    body = {"name": "김교수", "email": "t@example.test", "password": "correct-horse", field: value}
    with pytest.raises(ValidationError):
        SignupRequest.model_validate(body)


def test_signup_request_normalizes():
    req = SignupRequest.model_validate({"name": "  김교수 ", "email": " T@Example.Test ", "password": "p" * 128})
    assert (req.name, req.email) == ("김교수", "t@example.test")
