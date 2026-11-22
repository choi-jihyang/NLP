"""권한 확인(I7). 교수자는 자기 클래스만, 학생은 승인된 참여가 있는 클래스만."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus
from app.core.errors import AppError, ErrorCode
from app.models import ClassRoom, Enrollment, User


def own_class(db: Session, teacher: User, class_id: int) -> ClassRoom:
    klass = db.get(ClassRoom, class_id)
    if klass is None:
        raise AppError(ErrorCode.NOT_FOUND)
    if klass.teacher_id != teacher.seq:
        raise AppError(ErrorCode.FORBIDDEN)
    return klass


def find_enrollment(db: Session, class_id: int, student_id: int) -> Enrollment | None:
    return db.scalar(select(Enrollment).where(Enrollment.class_id == class_id, Enrollment.student_id == student_id))


def active_enrollment(db: Session, student: User, class_id: int) -> Enrollment:
    """승인된 참여만 통과. 대기 · 거절 · 내보낸 학생과 참여가 없는 학생은 FORBIDDEN."""
    enrollment = find_enrollment(db, class_id, student.seq)
    if enrollment is None or enrollment.status != EnrollmentStatus.APPROVED:
        raise AppError(ErrorCode.FORBIDDEN)
    return enrollment


def approved_count(db: Session, class_id: int) -> int:
    query = select(func.count()).select_from(Enrollment).where(
        Enrollment.class_id == class_id, Enrollment.status == EnrollmentStatus.APPROVED
    )
    return db.scalar(query) or 0
