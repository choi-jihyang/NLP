from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import EnrollmentStatus
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import TimestampMixin


class Enrollment(TimestampMixin, Base):
    """학생 한 명의 클래스 참여. created_at = 참여 요청 시각."""

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("class_id", "student_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_no: Mapped[str] = mapped_column(String(30))
    status: Mapped[EnrollmentStatus] = mapped_column(enum_column(EnrollmentStatus))
    decided_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    consented_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    removed_at: Mapped[datetime | None] = mapped_column(KstDateTime())
