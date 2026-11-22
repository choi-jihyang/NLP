"""상태·종류 값. DB에는 대문자 문자열로 저장한다 (schema.md "Enum")."""

from enum import StrEnum


class Role(StrEnum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class PlanCode(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class PaymentKind(StrEnum):
    NEW = "NEW"
    EXTEND = "EXTEND"


class JoinMode(StrEnum):
    APPROVAL = "APPROVAL"
    OPEN = "OPEN"


class EnrollmentStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REMOVED = "REMOVED"


class HintMode(StrEnum):
    NONE = "NONE"
    CONCEPT = "CONCEPT"
    STEP = "STEP"
    EARNED = "EARNED"


class HintPenalty(StrEnum):
    NONE = "NONE"
    PER_STEP = "PER_STEP"
    PRACTICE = "PRACTICE"


class PromptMode(StrEnum):
    FORM = "FORM"
    CUSTOM = "CUSTOM"
