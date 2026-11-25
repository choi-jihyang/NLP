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


class ChatRole(StrEnum):
    STUDENT = "STUDENT"
    ASSISTANT = "ASSISTANT"


class PasteField(StrEnum):
    ANSWER = "ANSWER"
    CHAT = "CHAT"
    CONCEPT_CHECK = "CONCEPT_CHECK"


class ResponseMode(StrEnum):
    """DB·API에는 대문자 문자열로 나간다 (schema.md Enum, api-contract 결정 B)."""

    NEXT_STEP = "NEXT_STEP"
    """일반 학습 도움: 설정된 단계 안내 정책대로 응답"""
    HINT_ONLY = "HINT_ONLY"
    """완성 답안 요청 + 시도 근거 없음 + 도움 방식을 고름: 힌트 위주로만 응답"""
    ASK_ATTEMPT = "ASK_ATTEMPT"
    """판단이 모호함: LLM 호출 없이 시도 여부를 되묻는다"""
    OFF_TOPIC = "OFF_TOPIC"
    """학습과 무관한 대화: LLM 호출 없이 과제로 돌려보낸다"""
    USAGE_LIMIT = "USAGE_LIMIT"
    """사용량 상한: LLM 호출 없이 안내 (I6). 판단은 채팅 service가 분류 전에 한다"""
    OFFER_CHOICES = "OFFER_CHOICES"
    """완성 답안 요청 + 시도 근거 없음 + 아직 고르지 않음: LLM 없이 도움 방식 고르기"""


class HelpChoice(StrEnum):
    """OFFER_CHOICES 뒤 학생이 고르는 도움 방식. 어느 것을 골라도 정책은 HINT_ONLY (I1)."""

    FIRST_HINT = "FIRST_HINT"
    FEEDBACK = "FEEDBACK"
    ORIGINAL = "ORIGINAL"
