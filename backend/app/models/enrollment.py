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
    __table_args__ = (UniqueConstraint("class_id", "student_no"), UniqueConstraint("class_id", "student_id"))

    seq: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.seq"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.seq"))
    student_no: Mapped[str] = mapped_column(String(30))
    status: Mapped[EnrollmentStatus] = mapped_column(enum_column(EnrollmentStatus))
    decided_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    consented_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    removed_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    # 다시 입장 대기 티켓(schema D21). 원문은 저장하지 않고 SHA-256 해시만
    reentry_ticket_hash: Mapped[str | None] = mapped_column(String(64))
    reentry_requested_at: Mapped[datetime | None] = mapped_column(KstDateTime())
    reentry_approved_at: Mapped[datetime | None] = mapped_column(KstDateTime())
