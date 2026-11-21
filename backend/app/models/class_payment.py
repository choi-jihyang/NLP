from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import PaymentKind, PlanCode
from app.db.session import Base
from app.db.types import KstDateTime, enum_column
from app.models.base import CreatedAtMixin


class ClassPayment(CreatedAtMixin, Base):
    """결제 목업. 실제 PG 연동 없음. class_id는 개설 전 결제라 비어 있을 수 있다."""

    __tablename__ = "class_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"))
    plan: Mapped[PlanCode] = mapped_column(enum_column(PlanCode))
    student_limit: Mapped[int]
    kind: Mapped[PaymentKind] = mapped_column(enum_column(PaymentKind))
    amount: Mapped[int]
    period_start: Mapped[datetime] = mapped_column(KstDateTime())
    period_end: Mapped[datetime] = mapped_column(KstDateTime())
