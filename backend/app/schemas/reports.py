"""이해 확인 · 리포트 · 학생별 기록 응답 (frontend/src/api/understanding.ts · reports.ts와 같은 모양).

question_index는 0부터. 문장 칸(reason · note · summary · cause · next_steps)은 저장된 데이터로 만든
규칙 기반 문장이다(LLM 아님 — PR 논의 사항).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ConceptStatus, Confidence, QuestionType

# ---------- 이해 확인 (학생) ----------


class CheckItem(BaseModel):
    question_id: int
    type: Literal[QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER]
    prompt: str
    code: str
    choices: list[str]


class UnderstandingCheckOut(BaseModel):
    explain_prompt: str
    explain_code: str
    items: list[CheckItem]
    submitted: bool


class CheckAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int
    value: str = Field(max_length=5_000)
    confidence: Confidence | None = None


class CheckSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str = Field(default="", max_length=10_000)
    answers: list[CheckAnswerIn] = Field(default_factory=list, max_length=50)


class CheckReceipt(BaseModel):
    submitted_at: datetime


# ---------- 반 리포트 (교수자) ----------


class QuestionStat(BaseModel):
    question_index: int
    type_label: str
    correct_rate: int
    variant_rate: int | None
    """확인 문제가 없는 문항이면 null(화면: 확인 문제 없음)"""
    avg_hint_steps: float


class MistakeRow(BaseModel):
    label: str
    rate: int
    note: str | None
    correct: bool


class QuestionMistakes(BaseModel):
    question_index: int
    kind: Literal["CHOICE", "ANSWER", "TEST"]
    rows: list[MistakeRow]


class Supplement(BaseModel):
    question_index: int
    rate: int
    summary: str
    items: list[str]


class DependencyRow(BaseModel):
    student_id: int
    student_name: str
    question_index: int
    hint_steps: int
    variant_answer: str
    cause: str


class SignalRow(BaseModel):
    student_id: int
    student_name: str
    question_index: int
    signals: list[str]


class AssignmentReport(BaseModel):
    assignment_id: int
    title: str
    submitted_count: int
    student_count: int
    assisted_correct_rate: int
    alone_variant_rate: int | None
    """과제에 확인 문제가 하나도 없으면 null"""
    concept_check_ok_rate: int
    question_stats: list[QuestionStat]
    mistakes: list[QuestionMistakes]
    supplement: Supplement | None
    dependency: list[DependencyRow]
    signals: list[SignalRow]


# ---------- 학생별 기록 (교수자) ----------


class RecordRow(BaseModel):
    question_index: int
    hint_steps: int
    result: str
    variant: str
    concept_check: str
    signal: str | None


class RecordTurn(BaseModel):
    message: str
    classification: str
    attempt: bool
    leak_blocked: bool


class RecordConversation(BaseModel):
    question_index: int
    turns: list[RecordTurn]
    note: str


class StudentRecord(BaseModel):
    student_id: int
    student_name: str
    assignment_title: str
    score: int
    max_score: int
    pending_points: int
    variant_passed: int
    variant_total: int
    variant_note: str
    hint_steps: int
    class_avg_hint_steps: float
    rows: list[RecordRow]
    conversation: RecordConversation | None


# ---------- 내 리포트 (학생, 결과 공개 뒤) ----------


class ConceptRow(BaseModel):
    name: str
    status: ConceptStatus
    reason: str


class MyQuestionResult(BaseModel):
    question_index: int
    type_label: str
    result: str
    correct_answer: str


class MyReport(BaseModel):
    released: Literal[True] = True
    assignment_title: str
    score: int
    max_score: int
    pending_points: int
    hint_steps: int
    concepts: list[ConceptRow]
    misconceptions: list[str]
    overconfident: list[str]
    next_steps: list[str]
    questions: list[MyQuestionResult]


class MyReportPending(BaseModel):
    released: Literal[False] = False
    assignment_title: str
