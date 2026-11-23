from typing import Any

from sqlalchemy import JSON, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import QuestionType
from app.db.session import Base
from app.db.types import enum_column
from app.models.base import TimestampMixin


class Question(TimestampMixin, Base):
    """문항. 학생에게 보내면 안 되는 값은 모두 answer_key(JSON)에만 둔다(schema D17, I8)."""

    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("assignment_id", "position"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.seq"))
    position: Mapped[int]
    type: Mapped[QuestionType] = mapped_column(enum_column(QuestionType))
    points: Mapped[int]
    prompt: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text, default="")
    choices: Mapped[list[str]] = mapped_column(JSON, default=list)
    starter_code: Mapped[str] = mapped_column(Text, default="")
    public_tests: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)  # [{input, expected_output}]
    ai_help: Mapped[bool] = mapped_column(default=True)
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # 🔒 AnswerKey
