from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ChatRole, HelpChoice, PasteField, ResponseMode
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import CreatedAtMixin


class ChatMessage(CreatedAtMixin, Base):
    """문항별 대화 한 줄. 🔒 분류 결과 · 누출 검사 결과는 학생 응답에 넣지 않는다."""

    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_answer_created", "answer_id", "created_at"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.seq"))
    role: Mapped[ChatRole] = mapped_column(enum_column(ChatRole))
    content: Mapped[str] = mapped_column(Text, default="")
    help_choice: Mapped[HelpChoice | None] = mapped_column(enum_column(HelpChoice), default=None)
    response_mode: Mapped[ResponseMode | None] = mapped_column(enum_column(ResponseMode), default=None)
    hint_step: Mapped[int | None] = mapped_column(default=None)
    is_learning_context: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    requests_complete_answer: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    has_self_attempt_evidence: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    uncertain: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    confidence: Mapped[float | None] = mapped_column(default=None)  # 🔒
    leak_blocked: Mapped[bool | None] = mapped_column(default=None)  # 🔒
    blocked_draft: Mapped[str | None] = mapped_column(Text, default=None)  # 🔒


class PasteEvent(CreatedAtMixin, Base):
    """붙여넣기 기록. 내용 컬럼 없음(I5) — 길이와 시점만."""

    __tablename__ = "paste_events"

    seq: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.seq"))
    field: Mapped[PasteField] = mapped_column(enum_column(PasteField))
    length: Mapped[int]
    pasted_at: Mapped[datetime] = mapped_column(KstDateTime())
