"""요금제 · 결제 · 클래스 · 명단 요청/응답. id 필드는 seq(숫자)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import JoinMode, PlanCode
from app.schemas.enrollments import normalize_student_no


class PlanOut(BaseModel):
    code: PlanCode
    name: str
    student_limit: int
    price: int


class PaymentCreate(BaseModel):
    plan: PlanCode
    kind: Literal["NEW", "EXTEND"]
    class_id: int | None = None
    """EXTEND일 때 연장할 내 클래스. NEW에는 쓰지 않는다"""

    @model_validator(mode="after")
    def _class_for_extend(self) -> "PaymentCreate":
        if (self.kind == "EXTEND") != (self.class_id is not None):
            raise ValueError("연장(EXTEND)에만 class_id를 보냅니다.")
        return self


class PaymentOut(BaseModel):
    payment_seq: int
    plan: PlanCode
    student_limit: int
    amount: int
    class_id: int | None = None
    expires_at: datetime | None = None
    """EXTEND: 늘어난 만료 시각"""


class ClassCreate(BaseModel):
    name: str
    starts_on: date
    payment_seq: int

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 100:
            raise ValueError("클래스 이름은 1–100자여야 합니다.")
        return value


class ClassInfo(BaseModel):
    seq: int
    name: str
    invite_code: str
    plan: PlanCode
    student_limit: int
    student_count: int
    starts_at: datetime
    expires_at: datetime


class RosterEntry(BaseModel):
    student_no: str
    is_use: bool = True

    @field_validator("student_no")
    @classmethod
    def _student_no(cls, value: str) -> str:
        return normalize_student_no(value)


class RosterSettings(BaseModel):
    join_mode: JoinMode
    roster: list[RosterEntry] = Field(max_length=1000)
