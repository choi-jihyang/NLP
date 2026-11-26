"""학생 제출 요청/응답 (api-contract "풀이 · 제출"). 결과 공개 전 정오 · 점수 · 숨김 테스트 결과 필드는 없다."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AnswerStatus

MAX_ANSWER = 20_000


class ConceptCheckState(BaseModel):
    questions: list[str]
    answered: int
    """답한 질문 수. questions[answered]가 지금 답할 질문"""


class AnswerState(BaseModel):
    question_id: int
    content: str
    status: AnswerStatus
    submitted_at: datetime | None
    submit_count: int
    hint_step: int
    concept_check: ConceptCheckState | None


class SubmissionOut(BaseModel):
    assignment_id: int
    answers: dict[int, AnswerState]
    """문항 seq → 내 답. 아직 활동하지 않은 문항은 없다"""
    finalized: bool
    results_released: bool


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(max_length=MAX_ANSWER)


class PublicTestResult(BaseModel):
    input: str
    expected_output: str
    actual_output: str | None
    passed: bool
    error: str | None


class RunOut(BaseModel):
    ok: bool
    error: str | None
    """컴파일 오류 등 테스트를 돌리지 못한 이유"""
    results: list[PublicTestResult]


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(max_length=MAX_ANSWER)


class ConceptReplyBody(BaseModel):
    """붙여넣기 여부는 받지 않는다 — /paste-events(field = CONCEPT_CHECK)로만 (I5)."""

    model_config = ConfigDict(extra="forbid")

    reply: str = Field(min_length=1, max_length=5_000)
    elapsed_ms: int = Field(ge=0, le=24 * 3600 * 1000)
