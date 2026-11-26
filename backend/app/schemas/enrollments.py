"""학생 입장 · 참여 요청 · 내 클래스 요청/응답. id 필드는 seq(숫자)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.enums import EnrollmentStatus


def normalize_student_no(value: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 30 or any(ch.isspace() for ch in value):
        raise ValueError("학번은 공백 없이 1–30자여야 합니다.")
    return value


class JoinBody(BaseModel):
    invite_code: str = Field(max_length=20)
    student_no: str

    @field_validator("student_no")
    @classmethod
    def _student_no(cls, value: str) -> str:
        return normalize_student_no(value)


class JoinOut(BaseModel):
    class_id: int
    class_name: str
    status: EnrollmentStatus
    access_token: str | None  # 다시 입장 요청이면 null — 대신 reentry_ticket
    reentry_ticket: str | None = None


class ReentryBody(BaseModel):
    ticket: str = Field(min_length=1, max_length=100)


class ReentryOut(BaseModel):
    status: EnrollmentStatus
    access_token: str | None


class JoinRequestOut(BaseModel):
    seq: int
    student_no: str
    requested_at: datetime
    is_reentry: bool


class DecisionBody(BaseModel):
    approve: bool


class StatusOut(BaseModel):
    status: EnrollmentStatus


class StudentOut(BaseModel):
    seq: int
    student_no: str


class OkOut(BaseModel):
    ok: bool = True


class MyClassOut(BaseModel):
    class_id: int
    class_name: str
    student_no: str
    enrollment_status: EnrollmentStatus
    assignments: list["MyAssignmentOut"] = Field(default_factory=list)  # 승인된 클래스의 배포된 과제


class MyAssignmentOut(BaseModel):
    """학생 "내 과제" 한 줄. 점수는 결과 공개 뒤에만(score_text)."""

    seq: int
    title: str
    language: str
    status: Literal["IN_PROGRESS", "FINALIZED", "RELEASED"]
    due_at: datetime | None
    hint_mode: str
    hint_mode_label: str
    submitted: int
    total: int
    score_text: str | None
