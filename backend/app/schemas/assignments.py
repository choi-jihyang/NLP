"""교수자 과제 요청/응답. 정답·숨김 테스트 포함 — 학생 응답에는 쓰지 않는다(student_assignments.py)."""

import re
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator

from app.core.enums import HintMode, Language, QuestionType
from app.schemas.ai_policy import AiPolicy

MAX_IO = 10_000
MAX_CODE = 20_000
_CHOICE_INDEX = re.compile(r"0|[1-9][0-9]*")  # ASCII 정규형만: "٣" · "１" · "01" 거부


def check_choice_answer(choices: list[str], answer: str) -> None:
    """객관식 · 확인 문제 공통: 선택지 2개 이상, 정답은 선택지 번호('0'부터)."""
    if len(choices) < 2:
        raise ValueError("객관식은 선택지가 2개 이상이어야 합니다.")
    if not (_CHOICE_INDEX.fullmatch(answer) and int(answer) < len(choices)):
        raise ValueError("객관식 정답은 선택지 번호('0'부터)여야 합니다.")


def not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("비어 있으면 안 됩니다.")
    return value


class IOTest(BaseModel):
    """테스트 한 건: 표준 입력 → 표준 출력 (④ 설계 A1)."""

    input: str = Field(default="", max_length=MAX_IO)
    expected_output: str = Field(min_length=1, max_length=MAX_IO)

    _expected_not_blank = field_validator("expected_output")(not_blank)  # 줄 끝 공백은 비교에서 무시(A2)


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

    _prompt_not_blank = field_validator("prompt")(not_blank)

    @model_validator(mode="after")
    def _rules_by_type(self) -> "Variant":
        if self.type == QuestionType.MULTIPLE_CHOICE:
            check_choice_answer(self.choices, self.answer)
        elif not self.answer.strip():
            raise ValueError("확인 문제는 정답이 있어야 합니다.")
        return self


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

    _prompt_not_blank = field_validator("prompt")(not_blank)

    @model_validator(mode="after")
    def _rules_by_type(self) -> "QuestionData":
        if self.type == QuestionType.MULTIPLE_CHOICE:
            check_choice_answer(self.choices, self.answer)
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
