"""참여 요청 수락·거절 · 학생 목록 · 내보내기 · 참여 상태 · 동의 · 내 클래스."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus
from app.core.errors import AppError, ErrorCode
from app.models import ClassRoom, Enrollment, User
from app.services.access import active_enrollment, approved_count, find_enrollment, own_class
from app.services.join_service import clear_reentry


@dataclass(frozen=True)
class MyClassView:
    enrollment: Enrollment
    klass: ClassRoom


def is_reentry(enrollment: Enrollment) -> bool:
    """다시 입장 요청 = 티켓이 있고 아직 수락 전 (③ 설계 C2)."""
    return enrollment.reentry_ticket_hash is not None and enrollment.reentry_approved_at is None


def requested_at(enrollment: Enrollment) -> datetime:
    if is_reentry(enrollment) and enrollment.reentry_requested_at is not None:
        return enrollment.reentry_requested_at
    return enrollment.updated_at


def list_requests(db: Session, teacher: User, class_id: int) -> list[Enrollment]:
    klass = own_class(db, teacher, class_id)
    reentry_waiting = Enrollment.reentry_ticket_hash.is_not(None) & Enrollment.reentry_approved_at.is_(None)
    query = select(Enrollment).where(
        Enrollment.class_id == klass.seq,
        (Enrollment.status == EnrollmentStatus.PENDING) | reentry_waiting,
    )
    return sorted(db.scalars(query), key=lambda e: (requested_at(e), e.seq))


def decide_request(db: Session, teacher: User, class_id: int, enrollment_seq: int, approve: bool) -> Enrollment:
    klass = own_class(db, teacher, class_id)
    enrollment = db.get(Enrollment, enrollment_seq)
    if enrollment is None or enrollment.class_id != klass.seq:
        raise AppError(ErrorCode.NOT_FOUND)
    if is_reentry(enrollment):  # 참여 상태 · 정원은 건드리지 않는다
        if approve:
            enrollment.reentry_approved_at = now_kst()
        else:
            clear_reentry(enrollment)
        db.commit()
        return enrollment
    if enrollment.status != EnrollmentStatus.PENDING:
        raise AppError(ErrorCode.NOT_FOUND)
    if approve:
        if approved_count(db, klass.seq) >= klass.student_limit:
            raise AppError(ErrorCode.CLASS_FULL)
        enrollment.status = EnrollmentStatus.APPROVED
        enrollment.decided_at = now_kst()
    else:
        enrollment.status = EnrollmentStatus.REJECTED
        enrollment.decided_at = now_kst()
    db.commit()
    return enrollment


def list_students(db: Session, teacher: User, class_id: int) -> list[Enrollment]:
    klass = own_class(db, teacher, class_id)
    query = select(Enrollment).where(
        Enrollment.class_id == klass.seq, Enrollment.status == EnrollmentStatus.APPROVED
    ).order_by(Enrollment.student_no)
    return list(db.scalars(query))


def remove_student(db: Session, teacher: User, class_id: int, student_id: int) -> None:
    """내보내기. 답·대화 기록은 지우지 않는다."""
    klass = own_class(db, teacher, class_id)
    enrollment = find_enrollment(db, klass.seq, student_id)
    if enrollment is None or enrollment.status == EnrollmentStatus.REMOVED:
        raise AppError(ErrorCode.NOT_FOUND)
    enrollment.status = EnrollmentStatus.REMOVED
    enrollment.removed_at = now_kst()
    clear_reentry(enrollment)
    db.commit()


def my_enrollment(db: Session, student: User, class_id: int) -> Enrollment:
    enrollment = find_enrollment(db, class_id, student.seq)
    if enrollment is None:
        raise AppError(ErrorCode.NOT_FOUND)
    return enrollment


def consent(db: Session, student: User, class_id: int) -> Enrollment:
    enrollment = active_enrollment(db, student, class_id)
    if enrollment.consented_at is None:
        enrollment.consented_at = now_kst()
        db.commit()
    return enrollment


def my_classes(db: Session, student: User) -> list[MyClassView]:
    query = (
        select(Enrollment, ClassRoom)
        .join(ClassRoom, ClassRoom.seq == Enrollment.class_id)
        .where(
            Enrollment.student_id == student.seq,
            Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING]),
        )
        .order_by(Enrollment.created_at.desc(), Enrollment.seq.desc())
    )
    return [MyClassView(enrollment, klass) for enrollment, klass in db.execute(query).all()]
