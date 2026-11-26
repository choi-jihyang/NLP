from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Language
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import TimestampMixin
from app.schemas.ai_policy import default_ai_policy


class Assignment(TimestampMixin, Base):
    """과제. published_at이 없으면 초안, results_released_at이 있으면 결과 공개."""

    __tablename__ = "assignments"

    seq: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.seq"))
    title: Mapped[str] = mapped_column(String(100))
    course: Mapped[str] = mapped_column(String(100), default="")
    audience: Mapped[str] = mapped_column(String(100), default="")
    language: Mapped[Language] = mapped_column(enum_column(Language))
    description: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=default_ai_policy)
    published_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    results_released_at: Mapped[datetime | None] = mapped_column(KstDateTime())
