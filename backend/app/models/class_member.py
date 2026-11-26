from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin


class ClassMember(TimestampMixin, Base):
    """교수자가 미리 넣어 둔 학번 명단. 빼는 것은 삭제 대신 is_use = False."""

    __tablename__ = "class_members"
    __table_args__ = (UniqueConstraint("class_id", "student_no"),)

    seq: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.seq"))
    student_no: Mapped[str] = mapped_column(String(30))
    is_use: Mapped[bool] = mapped_column(default=True)
