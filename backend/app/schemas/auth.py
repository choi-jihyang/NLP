"""가입·로그인 요청/응답. 응답 id 필드는 seq(숫자)."""

import re

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import Role
from app.services.auth_service import normalize_email

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 100:
            raise ValueError("이름은 1–100자여야 합니다.")
        return value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        value = normalize_email(value)
        if len(value) > 255 or not _EMAIL.match(value):
            raise ValueError("이메일 형식이 올바르지 않습니다.")
        return value

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        if not 8 <= len(value) <= 128:
            raise ValueError("비밀번호는 8–128자여야 합니다.")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("비밀번호에 쓸 수 없는 문자가 있습니다.") from exc
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq: int
    name: str
    email: str | None
    role: Role


class AuthResponse(BaseModel):
    access_token: str
    user: UserOut
