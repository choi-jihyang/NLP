from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AnswerStatus, ConceptStatus
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import CreatedAtMixin, TimestampMixin


class Submission(TimestampMixin, Base):
    """학생 한 명의 과제 하나에 대한 제출. finalized_at 이후 답 수정 · AI 도움 잠김."""

    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "enrollment_id"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.seq"))
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.seq"))
    finalized_at: Mapped[datetime | None] = mapped_column(KstDateTime())


class Answer(TimestampMixin, Base):
    """문항 하나의 현재 답. 다시 제출하면 덮어쓴다(이력 없음). 🔒 컬럼은 결과 공개 전 학생에게 보내지 않는다."""

    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("submission_id", "question_id"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.seq"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.seq"))
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[AnswerStatus] = mapped_column(enum_column(AnswerStatus), default=AnswerStatus.DRAFT)
    submit_count: Mapped[int] = mapped_column(default=0)
    submitted_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    hint_step: Mapped[int] = mapped_column(default=0)
    is_correct: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    test_results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)  # 🔒 숨김 포함
    score: Mapped[int | None] = mapped_column(default=None)  # 🔒
    feedback: Mapped[str | None] = mapped_column(Text, default=None)  # 🔒
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.seq"), default=None)
    graded_at: Mapped[datetime | None] = mapped_column(KstDateTime())


class ConceptCheckItem(CreatedAtMixin, Base):
    """제출 전 개념 확인 질문 하나. 점수에 반영하지 않는다."""

    __tablename__ = "concept_check_items"
    __table_args__ = (UniqueConstraint("answer_id", "position"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.seq"))
    position: Mapped[int]
    question_text: Mapped[str] = mapped_column(Text)
    reply: Mapped[str | None] = mapped_column(Text, default=None)
    elapsed_ms: Mapped[int | None] = mapped_column(default=None)
    ai_written_score: Mapped[float | None] = mapped_column(default=None)  # 🔒 NLP 담당 확인 필요(scope ②)
    judgement: Mapped[ConceptStatus | None] = mapped_column(enum_column(ConceptStatus), default=None)  # 🔒
    answered_at: Mapped[datetime | None] = mapped_column(KstDateTime())
