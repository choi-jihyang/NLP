"""교수자 가입·로그인. FastAPI에 의존하지 않는다(AppError만 던짐)."""

from dataclasses import dataclass
from datetime import timedelta
from functools import cache

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.config import get_settings
from app.core.enums import Role
from app.core.errors import AppError, ErrorCode
from app.core.security import hash_password, verify_password
from app.core.tokens import issue_token
from app.models.user import User


@dataclass(frozen=True)
class AuthResult:
    access_token: str
    user: User


def normalize_email(email: str) -> str:
    return email.strip().lower()


@cache
def _dummy_hash() -> str:
    """계정이 없을 때도 같은 비용의 해시 계산을 하기 위한 값(비밀 아님)."""
    return hash_password("thinkguard-dummy-password")


def _login_token(user: User) -> str:
    return issue_token(user, now_kst() + timedelta(hours=get_settings().teacher_token_hours))


def signup(db: Session, name: str, email: str, password: str) -> AuthResult:
    email = normalize_email(email)
    if db.scalar(select(User.seq).where(User.email == email)) is not None:
        raise AppError(ErrorCode.EMAIL_TAKEN)
    user = User(role=Role.TEACHER, email=email, password_hash=hash_password(password), name=name, login_at=now_kst())
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # 동시에 같은 이메일로 가입
        db.rollback()
        raise AppError(ErrorCode.EMAIL_TAKEN) from exc
    return AuthResult(_login_token(user), user)


def login(db: Session, email: str, password: str) -> AuthResult:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    stored = user.password_hash if user is not None else None
    if user is None or stored is None:
        verify_password(password, _dummy_hash())
        raise AppError(ErrorCode.INVALID_CREDENTIALS)
    if not verify_password(password, stored):
        raise AppError(ErrorCode.INVALID_CREDENTIALS)
    user.login_at = now_kst()
    db.commit()
    return AuthResult(_login_token(user), user)
