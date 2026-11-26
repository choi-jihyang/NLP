from datetime import datetime

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Confidence
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import CreatedAtMixin


class UnderstandingCheck(CreatedAtMixin, Base):
    """최종 제출 뒤 AI 없이 보는 이해 확인(내 코드 설명 + 확인 문제 + 자신감). 제출당 한 번."""

    __tablename__ = "understanding_checks"

    seq: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.seq"), unique=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(KstDateTime())


class UnderstandingAnswer(CreatedAtMixin, Base):
    __tablename__ = "understanding_answers"
    __table_args__ = (UniqueConstraint("check_id", "question_id"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("understanding_checks.seq"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.seq"))
    value: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[Confidence | None] = mapped_column(enum_column(Confidence), default=None)
    is_correct: Mapped[bool] = mapped_column(default=False)  # 🔒 결과 공개 뒤 내 리포트에서만
