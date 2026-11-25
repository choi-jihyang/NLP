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


class Language(StrEnum):
    """과제 언어. 코드 실행기가 실행 환경을 고르는 기준(schema D16)."""

    PYTHON = "PYTHON"
    JAVA = "JAVA"
    C = "C"
    JAVASCRIPT = "JAVASCRIPT"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"  # 객관식 퀴즈
    SHORT_ANSWER = "SHORT_ANSWER"  # 출력 예측
    CODE = "CODE"  # 코드 작성(테스트 실행)
    PROJECT = "PROJECT"  # 간단 제작(교수자 채점)


class AnswerStatus(StrEnum):
    DRAFT = "DRAFT"
    AWAITING_CHECK = "AWAITING_CHECK"  # 힌트 없이 처음 낸 문항: 개념 확인 답변 대기
    SUBMITTED = "SUBMITTED"


class ConceptStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    NEEDS_WORK = "NEEDS_WORK"
    UNCLEAR = "UNCLEAR"
