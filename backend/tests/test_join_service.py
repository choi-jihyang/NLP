from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus, JoinMode, Role
from app.core.errors import AppError, ErrorCode
from app.core.tokens import decode_token
from app.models import Enrollment, User
from app.services.join_service import claim_reentry, join
from tests.factories import add_member, enroll, make_class, make_student, make_teacher


def _error(*args: object) -> ErrorCode:
    with pytest.raises(AppError) as info:
        join(*args)  # type: ignore[arg-type]
    return info.value.code


def _count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_roster_member_joins_approved(db: Session):
    klass = make_class(db, make_teacher(db))
    add_member(db, klass, "20260001")
    result = join(db, "TG-1000", "20260001", None)
    assert result.enrollment.status == EnrollmentStatus.APPROVED and result.enrollment.decided_at is not None
    student = db.get(User, result.enrollment.student_id)
    assert student is not None and (student.role, student.name, student.email) == (Role.STUDENT, "20260001", None)
    assert student.login_at is not None
    assert decode_token(result.access_token).user_seq == student.seq


def test_invite_code_is_normalized(db: Session):
    klass = make_class(db, make_teacher(db))
    assert join(db, " tg-1000 ", "20260001", None).klass.seq == klass.seq


def test_unknown_student_waits(db: Session):
    make_class(db, make_teacher(db))
    result = join(db, "TG-1000", "20269999", None)
    assert result.enrollment.status == EnrollmentStatus.PENDING and result.enrollment.decided_at is None


def test_open_mode_approves(db: Session):
    make_class(db, make_teacher(db), join_mode=JoinMode.OPEN)
    assert join(db, "TG-1000", "20269999", None).enrollment.status == EnrollmentStatus.APPROVED


def test_unknown_code(db: Session):
    assert _error(db, "TG-0000", "1", None) == ErrorCode.INVITE_CODE_INVALID


def test_not_started_and_expired(db: Session):
    teacher = make_teacher(db)
    make_class(db, teacher, code="TG-2000", starts_at=now_kst() + timedelta(days=3))
    past = now_kst() - timedelta(days=400)
    make_class(db, teacher, code="TG-3000", starts_at=past, expires_at=past + timedelta(days=365))
    assert _error(db, "TG-2000", "1", None) == ErrorCode.CLASS_NOT_STARTED
    assert _error(db, "TG-3000", "1", None) == ErrorCode.CLASS_EXPIRED


def test_full_class_rejects_and_creates_nothing(db: Session):
    klass = make_class(db, make_teacher(db), limit=1)
    enroll(db, klass, make_student(db, "X"), "X")
    add_member(db, klass, "A")
    users, enrollments = _count(db, User), _count(db, Enrollment)
    assert _error(db, "TG-1000", "A", None) == ErrorCode.CLASS_FULL
    assert (_count(db, User), _count(db, Enrollment)) == (users, enrollments)


def test_removed_number_is_forbidden(db: Session):
    klass = make_class(db, make_teacher(db))
    enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.REMOVED)
    assert _error(db, "TG-1000", "A", None) == ErrorCode.FORBIDDEN


def test_teacher_token_cannot_join(db: Session):
    teacher = make_teacher(db)
    make_class(db, teacher)
    assert _error(db, "TG-1000", "A", teacher) == ErrorCode.FORBIDDEN


def test_same_account_rejoin_keeps_enrollment(db: Session):
    make_class(db, make_teacher(db))
    first = join(db, "TG-1000", "A", None)
    student = db.get(User, first.enrollment.student_id)
    users = _count(db, User)
    again = join(db, "TG-1000", "A", student)
    assert again.enrollment.seq == first.enrollment.seq
    assert again.enrollment.status == EnrollmentStatus.PENDING
    assert _count(db, User) == users


def test_rejoin_without_token_gets_ticket_not_token(db: Session):
    klass = make_class(db, make_teacher(db))
    add_member(db, klass, "A")
    first = join(db, "TG-1000", "A", None)
    again = join(db, "TG-1000", "A", None)
    assert again.access_token is None  # 그 계정의 토큰은 수락 전까지 주지 않는다(리뷰 C1 · C2)
    assert again.reentry_ticket and again.status == EnrollmentStatus.PENDING
    assert again.enrollment.seq == first.enrollment.seq
    assert again.enrollment.status == EnrollmentStatus.APPROVED  # 원래 참여 · 자리는 그대로(리뷰 I1)
    assert again.enrollment.reentry_ticket_hash not in (None, again.reentry_ticket)  # 해시만 저장


def test_other_account_with_same_number_gets_ticket(db: Session):
    klass = make_class(db, make_teacher(db))
    add_member(db, klass, "A")
    join(db, "TG-1000", "A", None)
    again = join(db, "TG-1000", "A", make_student(db, "S"))
    assert again.access_token is None and again.reentry_ticket


def test_pending_number_without_token_also_gets_ticket(db: Session):
    # 대기 중인 계정도 다른 클래스에 승인돼 있을 수 있으므로 토큰을 주지 않는다(리뷰 C2)
    make_class(db, make_teacher(db))
    join(db, "TG-1000", "A", None)
    again = join(db, "TG-1000", "A", None)
    assert again.access_token is None and again.reentry_ticket


def test_second_number_in_same_class_is_already_enrolled(db: Session):
    make_class(db, make_teacher(db))
    first = join(db, "TG-1000", "A", None)
    student = db.get(User, first.enrollment.student_id)
    assert _error(db, "TG-1000", "B", student) == ErrorCode.ALREADY_ENROLLED


def test_existing_student_is_reused_in_another_class(db: Session):
    teacher = make_teacher(db)
    make_class(db, teacher, code="TG-1001")
    make_class(db, teacher, code="TG-1002")
    first = join(db, "TG-1001", "A", None)
    student = db.get(User, first.enrollment.student_id)
    users = _count(db, User)
    second = join(db, "TG-1002", "A", student)
    assert second.enrollment.student_id == student.seq
    assert _count(db, User) == users


def test_rejected_student_can_ask_again(db: Session):
    klass = make_class(db, make_teacher(db))
    student = make_student(db, "A")
    rejected = enroll(db, klass, student, "A", EnrollmentStatus.REJECTED, decided=True)
    again = join(db, "TG-1000", "A", student)
    assert again.enrollment.seq == rejected.seq
    assert again.enrollment.status == EnrollmentStatus.PENDING and again.enrollment.decided_at is None



def test_claim_before_approval_is_pending(db: Session):
    klass = make_class(db, make_teacher(db))
    add_member(db, klass, "A")
    join(db, "TG-1000", "A", None)
    ticket = join(db, "TG-1000", "A", None).reentry_ticket
    claimed = claim_reentry(db, ticket)
    assert (claimed.status, claimed.access_token) == (EnrollmentStatus.PENDING, None)


def test_unknown_ticket_is_not_found(db: Session):
    with pytest.raises(AppError) as info:
        claim_reentry(db, "no-such-ticket")
    assert info.value.code == ErrorCode.NOT_FOUND
