from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import KST
from app.core.enums import EnrollmentStatus, PaymentKind, PlanCode, Role
from app.core.security import verify_password
from app.models import ClassMember, ClassPayment, ClassRoom, Enrollment, User
from app.seed import (
    SEED_INVITE_CODE,
    SEED_ROSTER_ONLY_NO,
    SEED_STUDENT_NOS,
    SEED_TEACHER_EMAIL,
    SEED_TEACHER_PASSWORD,
    SeedAlreadyLoadedError,
    seed,
)


def _count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_seed_contents(db: Session):
    klass = seed(db, today=date(2026, 11, 21))

    teacher = db.scalar(select(User).where(User.email == SEED_TEACHER_EMAIL))
    assert teacher is not None and teacher.role == Role.TEACHER
    assert teacher.password_hash and verify_password(SEED_TEACHER_PASSWORD, teacher.password_hash)

    assert klass.invite_code == SEED_INVITE_CODE
    assert klass.plan == PlanCode.SMALL and klass.student_limit == 50
    assert klass.starts_at.isoformat() == "2026-11-21T00:00:00+09:00"
    assert klass.expires_at.isoformat() == "2027-11-21T00:00:00+09:00"
    assert klass.starts_at.tzinfo == KST

    payment = db.scalar(select(ClassPayment))
    assert payment is not None
    assert (payment.class_id, payment.kind, payment.amount) == (klass.seq, PaymentKind.NEW, 90_000)

    students = db.scalars(select(User).where(User.role == Role.STUDENT)).all()
    assert sorted(s.name for s in students) == sorted(SEED_STUDENT_NOS)
    assert all(s.email is None and s.password_hash is None for s in students)

    enrollments = db.scalars(select(Enrollment)).all()
    assert sorted(e.student_no for e in enrollments) == sorted(SEED_STUDENT_NOS)
    assert all(e.status == EnrollmentStatus.APPROVED and e.class_id == klass.seq for e in enrollments)

    members = {m.student_no for m in db.scalars(select(ClassMember)).all()}
    assert members == {*SEED_STUDENT_NOS, SEED_ROSTER_ONLY_NO}


def test_seed_twice_refuses(db: Session):
    seed(db, today=date(2026, 11, 21))
    with pytest.raises(SeedAlreadyLoadedError, match="이미"):
        seed(db, today=date(2026, 11, 21))
    assert _count(db, User) == 1 + len(SEED_STUDENT_NOS)
    assert _count(db, ClassRoom) == 1
