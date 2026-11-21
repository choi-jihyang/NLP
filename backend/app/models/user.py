from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Role
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    """교수자와 학생. 수업 코드로 입장한 학생은 email · password_hash가 NULL."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[Role] = mapped_column(enum_column(Role))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    login_at: Mapped[datetime | None] = mapped_column(KstDateTime())
