"""JWT(HS256) 발급·검증. 클레임: sub(str(user.seq)) · role · iat · exp."""

from dataclasses import dataclass
from datetime import datetime

import jwt

from app.core.clock import now_kst
from app.core.config import get_settings
from app.core.enums import Role
from app.core.errors import AppError, ErrorCode
from app.models.user import User

ALGORITHM = "HS256"
REQUIRED_CLAIMS = ["sub", "role", "iat", "exp"]


@dataclass(frozen=True)
class TokenClaims:
    user_seq: int
    role: Role


def issue_token(user: User, expires_at: datetime) -> str:
    """교수자: now_kst() + teacher_token_hours. 학생: ③이 클래스 expires_at을 넘긴다."""
    if expires_at.tzinfo is None:
        raise ValueError("expires_at에는 시간대가 있어야 합니다. now_kst() 기준으로 만드세요.")
    payload = {
        "sub": str(user.seq),
        "role": str(user.role),
        "iat": int(now_kst().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenClaims:
    """서명 · 만료 · 형식 · 클레임 값이 하나라도 틀리면 AppError(UNAUTHORIZED)."""
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret, algorithms=[ALGORITHM], options={"require": REQUIRED_CLAIMS}
        )
        return TokenClaims(user_seq=int(payload["sub"]), role=Role(payload["role"]))
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise AppError(ErrorCode.UNAUTHORIZED) from exc
