import pytest
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus
from app.core.errors import AppError, ErrorCode
from app.services.access import active_enrollment, approved_count, own_class
from tests.factories import enroll, make_class, make_student, make_teacher


def _code(fn: object, *args: object) -> ErrorCode:
    with pytest.raises(AppError) as info:
        fn(*args)  # type: ignore[operator]
    return info.value.code


def test_own_class_returns_class(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    assert own_class(db, teacher, klass.seq) is klass


def test_other_teachers_class_is_forbidden(db: Session):
    owner, other = make_teacher(db, "a@x.test"), make_teacher(db, "b@x.test")
    klass = make_class(db, owner)
    assert _code(own_class, db, other, klass.seq) == ErrorCode.FORBIDDEN


def test_missing_class_is_not_found(db: Session):
    assert _code(own_class, db, make_teacher(db), 999) == ErrorCode.NOT_FOUND


def test_approved_enrollment_is_active(db: Session):
    klass = make_class(db, make_teacher(db))
    student = make_student(db)
    enrollment = enroll(db, klass, student, "20260001")
    assert active_enrollment(db, student, klass.seq) is enrollment


@pytest.mark.parametrize("status", [EnrollmentStatus.PENDING, EnrollmentStatus.REJECTED, EnrollmentStatus.REMOVED])
def test_inactive_enrollment_is_forbidden(db: Session, status: EnrollmentStatus):
    klass = make_class(db, make_teacher(db))
    student = make_student(db)
    enroll(db, klass, student, "20260001", status)
    assert _code(active_enrollment, db, student, klass.seq) == ErrorCode.FORBIDDEN


def test_no_enrollment_is_forbidden(db: Session):
    klass = make_class(db, make_teacher(db))
    assert _code(active_enrollment, db, make_student(db), klass.seq) == ErrorCode.FORBIDDEN


def test_approved_count_counts_only_approved(db: Session):
    klass = make_class(db, make_teacher(db))
    enroll(db, klass, make_student(db, "a"), "a")
    enroll(db, klass, make_student(db, "b"), "b", EnrollmentStatus.PENDING)
    enroll(db, klass, make_student(db, "c"), "c", EnrollmentStatus.REMOVED)
    assert approved_count(db, klass.seq) == 1
