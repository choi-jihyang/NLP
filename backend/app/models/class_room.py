from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import JoinMode, PlanCode
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import TimestampMixin
from app.schemas.ai_policy import default_ai_policy


class ClassRoom(TimestampMixin, Base):
    """클래스 (테이블 이름 classes). class는 파이썬 예약어라 클래스 이름만 ClassRoom."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    invite_code: Mapped[str] = mapped_column(String(20), unique=True)
    plan: Mapped[PlanCode] = mapped_column(enum_column(PlanCode))
    student_limit: Mapped[int]
    join_mode: Mapped[JoinMode] = mapped_column(enum_column(JoinMode), default=JoinMode.APPROVAL)
    ai_defaults: Mapped[dict[str, Any]] = mapped_column(JSON, default=default_ai_policy)
    starts_at: Mapped[datetime] = mapped_column(KstDateTime())
    expires_at: Mapped[datetime] = mapped_column(KstDateTime())
