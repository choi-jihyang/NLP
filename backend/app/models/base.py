from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now_kst
from app.db.types import KstDateTime


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(KstDateTime(), default=now_kst)


class TimestampMixin(CreatedAtMixin):
    """수정되는 테이블: created_at + updated_at."""

    updated_at: Mapped[datetime] = mapped_column(KstDateTime(), default=now_kst, onupdate=now_kst)
