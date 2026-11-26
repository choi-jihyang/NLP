"""명단 · 입장 방식. 명단에서 빼면 지우지 않고 is_use = False (schema D15)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus, JoinMode
from app.models import ClassMember, ClassRoom, Enrollment, User
from app.services.access import approved_count, own_class


def get_roster(db: Session, teacher: User, class_id: int) -> tuple[JoinMode, list[ClassMember]]:
    klass = own_class(db, teacher, class_id)
    members = db.scalars(
        select(ClassMember).where(ClassMember.class_id == klass.seq).order_by(ClassMember.student_no)
    ).all()
    return klass.join_mode, list(members)


def save_roster(
    db: Session, teacher: User, class_id: int, join_mode: JoinMode, wanted: dict[str, bool]
) -> tuple[JoinMode, list[ClassMember]]:
    klass = own_class(db, teacher, class_id)
    klass.join_mode = join_mode
    existing = {m.student_no: m for m in db.scalars(select(ClassMember).where(ClassMember.class_id == klass.seq))}
    for student_no, member in existing.items():
        member.is_use = wanted.get(student_no, False)
    for student_no, is_use in wanted.items():
        if student_no not in existing:
            db.add(ClassMember(class_id=klass.seq, student_no=student_no, is_use=is_use))
    db.flush()
    _auto_approve_first_requests(db, klass)
    db.commit()
    return get_roster(db, teacher, class_id)


def _auto_approve_first_requests(db: Session, klass: ClassRoom) -> None:
    """사용 중인 명단에 있는 학번의 처음 참여 요청만, 오래된 순으로 정원 안에서 수락 (③ C3)."""
    active = select(ClassMember.student_no).where(ClassMember.class_id == klass.seq, ClassMember.is_use.is_(True))
    waiting = db.scalars(
        select(Enrollment)
        .where(
            Enrollment.class_id == klass.seq,
            Enrollment.status == EnrollmentStatus.PENDING,
            Enrollment.decided_at.is_(None),
            Enrollment.student_no.in_(active),
        )
        .order_by(Enrollment.created_at, Enrollment.seq)
    ).all()
    seats = max(klass.student_limit - approved_count(db, klass.seq), 0)
    now = now_kst()
    for enrollment in waiting[:seats]:
        enrollment.status = EnrollmentStatus.APPROVED
        enrollment.decided_at = now
