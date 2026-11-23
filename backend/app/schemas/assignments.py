"""교수자 과제 요청/응답. 정답·숨김 테스트 포함 — 학생 응답에는 쓰지 않는다(student_assignments.py)."""

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator

from app.core.enums import HintMode, Language, QuestionType
from app.schemas.ai_policy import AiPolicy

MAX_IO = 10_000
MAX_CODE = 20_000


class IOTest(BaseModel):
    """테스트 한 건: 표준 입력 → 표준 출력 (④ 설계 A1)."""

    input: str = Field(default="", max_length=MAX_IO)
    expected_output: str = Field(min_length=1, max_length=MAX_IO)


class TestCase(IOTest):
    __test__ = False  # pytest가 테스트 클래스로 모으지 않게

    hidden: bool = False


class Variant(BaseModel):
    """AI 없이 푸는 확인 문제."""

    type: Literal[QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER]
    prompt: str = Field(min_length=1)
    code: str = Field(default="", max_length=MAX_CODE)
    choices: list[str] = Field(default_factory=list, max_length=20)
    answer: str = Field(min_length=1)
    accepted_answers: list[str] = Field(default_factory=list)


class AnswerKey(BaseModel):
    """questions.answer_key — 학생에게 보내지 않는 값 전부."""

    answer: str | None = None
    accepted_answers: list[str] = Field(default_factory=list)
    misconceptions: dict[str, str] = Field(default_factory=dict)
    hidden_tests: list[IOTest] = Field(default_factory=list)
    rubric: list[str] = Field(default_factory=list)
    model_answer: str | None = None
    variant: Variant | None = None


class QuestionData(BaseModel):
    seq: int | None = None  # 응답에서만 채운다
    type: QuestionType
    points: int = Field(ge=0, le=1000)
    prompt: str = Field(min_length=1, max_length=MAX_CODE)
    code: str = Field(default="", max_length=MAX_CODE)
    choices: list[str] = Field(default_factory=list, max_length=20)
    answer: str = ""
    accepted_answers: list[str] = Field(default_factory=list)
    misconceptions: dict[str, str] = Field(default_factory=dict)
    starter_code: str = Field(default="", max_length=MAX_CODE)
    tests: list[TestCase] = Field(default_factory=list, max_length=50)
    rubric: list[str] = Field(default_factory=list)
    model_answer: str = Field(default="", max_length=MAX_CODE)
    ai_help: bool = True
    variant: Variant | None = None

    @model_validator(mode="after")
    def _rules_by_type(self) -> "QuestionData":
        if self.type == QuestionType.MULTIPLE_CHOICE:
            if len(self.choices) < 2:
                raise ValueError("객관식은 선택지가 2개 이상이어야 합니다.")
            if not (self.answer.isdecimal() and int(self.answer) < len(self.choices)):
                raise ValueError("객관식 정답은 선택지 번호('0'부터)여야 합니다.")
        elif self.type == QuestionType.SHORT_ANSWER and not self.answer.strip():
            raise ValueError("출력 예측 문항은 정답이 있어야 합니다.")
        elif self.type == QuestionType.CODE and not self.tests:
            raise ValueError("코드 작성 문항은 테스트가 1개 이상이어야 합니다.")
        elif self.type == QuestionType.PROJECT and not any(r.strip() for r in self.rubric):
            raise ValueError("간단 제작 문항은 채점 기준이 1개 이상이어야 합니다.")
        return self


class AssignmentData(BaseModel):
    """요청에서 seq · class_id · published · results_released는 무시한다(서버가 정함)."""

    seq: int | None = None
    class_id: int | None = None
    title: str
    course: str = Field(default="", max_length=100)
    audience: str = Field(default="", max_length=100)
    language: Language
    description: str = Field(default="", max_length=20_000)
    due_at: AwareDatetime | None = None
    published: bool = False
    results_released: bool = False
    policy: AiPolicy = Field(default_factory=AiPolicy)
    questions: list[QuestionData] = Field(default_factory=list, max_length=50)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 100:
            raise ValueError("과제 이름은 1–100자여야 합니다.")
        return value


class AssignmentSummary(BaseModel):
    seq: int
    title: str
    kinds: str
    status: Literal["DRAFT", "OPEN", "CLOSED"]
    due_at: datetime | None
    hint_mode: HintMode | None
    submitted_count: int = 0  # ⑦ 제출 API 전까지 0
    student_count: int
    todo: str | None = None
    results_released: bool


class DraftBody(BaseModel):
    source: Literal["BLANK"]  # SAMPLE은 ④-2(샘플 md 파서)에서


class PublishOut(BaseModel):
    invite_code: str


class ReleaseOut(BaseModel):
    results_released: bool = True
