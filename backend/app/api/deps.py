"""요청마다 토큰 → DB 사용자 · 역할 확인. 역할은 토큰이 아니라 DB 기준.

내보낸 학생(REMOVED)과 남의 클래스 접근(I7)은 ③ 클래스 API가 참여 상태로 막는다.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.core.errors import AppError, ErrorCode
from app.core.tokens import decode_token
from app.db.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)], db: DbSession
) -> User:
    if credentials is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    claims = decode_token(credentials.credentials)
    user = db.get(User, claims.user_seq)
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)], db: DbSession
) -> User | None:
    """토큰이 없거나 틀리거나 만료됐으면 None(401을 던지지 않음). 학생 입장에서만 쓴다."""
    if credentials is None:
        return None
    try:
        claims = decode_token(credentials.credentials)
    except AppError:
        return None
    return db.get(User, claims.user_seq)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_teacher(user: CurrentUser) -> User:
    if user.role != Role.TEACHER:
        raise AppError(ErrorCode.FORBIDDEN)
    return user


def require_student(user: CurrentUser) -> User:
    if user.role != Role.STUDENT:
        raise AppError(ErrorCode.FORBIDDEN)
    return user


TeacherUser = Annotated[User, Depends(require_teacher)]
StudentUser = Annotated[User, Depends(require_student)]
