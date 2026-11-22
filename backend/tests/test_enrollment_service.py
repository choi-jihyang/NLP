import pytest
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus
from app.core.errors import AppError, ErrorCode
from app.services.enrollment_service import (
    consent,
    decide_request,
    is_reentry,
    list_requests,
    list_students,
    my_classes,
    my_enrollment,
    remove_student,
)
from tests.factories import enroll, make_class, make_student, make_teacher


def _error(fn, *args) -> ErrorCode:  # noqa: ANN001
    with pytest.raises(AppError) as info:
        fn(*args)
    return info.value.code


def _setup(db: Session, limit: int = 50):  # noqa: ANN202
    teacher = make_teacher(db)
    return teacher, make_class(db, teacher, limit=limit)


def test_approve_request(db: Session):
    teacher, klass = _setup(db)
    waiting = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    result = decide_request(db, teacher, klass.seq, waiting.seq, True)
    assert result.status == EnrollmentStatus.APPROVED and result.decided_at is not None


def test_approve_when_full(db: Session):
    teacher, klass = _setup(db, limit=1)
    enroll(db, klass, make_student(db, "X"), "X")
    waiting = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    assert _error(decide_request, db, teacher, klass.seq, waiting.seq, True) == ErrorCode.CLASS_FULL


def test_reentry_approval_ignores_limit(db: Session):
    teacher, klass = _setup(db, limit=1)
    enroll(db, klass, make_student(db, "X"), "X")
    back = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING, decided=True)
    assert decide_request(db, teacher, klass.seq, back.seq, True).status == EnrollmentStatus.APPROVED


def test_reject_first_request(db: Session):
    teacher, klass = _setup(db)
    waiting = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    assert decide_request(db, teacher, klass.seq, waiting.seq, False).status == EnrollmentStatus.REJECTED


def test_reject_reentry_restores_approved(db: Session):
    teacher, klass = _setup(db)
    back = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING, decided=True)
    assert decide_request(db, teacher, klass.seq, back.seq, False).status == EnrollmentStatus.APPROVED


def test_decide_requires_pending_in_own_class(db: Session):
    teacher, klass = _setup(db)
    approved = enroll(db, klass, make_student(db, "A"), "A")
    assert _error(decide_request, db, teacher, klass.seq, approved.seq, True) == ErrorCode.NOT_FOUND
    assert _error(decide_request, db, teacher, klass.seq, 999, True) == ErrorCode.NOT_FOUND
    other = make_teacher(db, "o@x.test")
    assert _error(decide_request, db, other, klass.seq, approved.seq, True) == ErrorCode.FORBIDDEN


def test_list_requests_marks_reentry(db: Session):
    teacher, klass = _setup(db)
    first = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    back = enroll(db, klass, make_student(db, "B"), "B", EnrollmentStatus.PENDING, decided=True)
    enroll(db, klass, make_student(db, "C"), "C")
    requests = list_requests(db, teacher, klass.seq)
    assert {(e.seq, is_reentry(e)) for e in requests} == {(first.seq, False), (back.seq, True)}


def test_list_students_approved_only(db: Session):
    teacher, klass = _setup(db)
    enroll(db, klass, make_student(db, "B"), "B")
    enroll(db, klass, make_student(db, "A"), "A")
    enroll(db, klass, make_student(db, "C"), "C", EnrollmentStatus.PENDING)
    assert [e.student_no for e in list_students(db, teacher, klass.seq)] == ["A", "B"]


def test_remove_student(db: Session):
    teacher, klass = _setup(db)
    student = make_student(db, "A")
    enrollment = enroll(db, klass, student, "A")
    remove_student(db, teacher, klass.seq, student.seq)
    assert enrollment.status == EnrollmentStatus.REMOVED and enrollment.removed_at is not None
    assert _error(remove_student, db, teacher, klass.seq, student.seq) == ErrorCode.NOT_FOUND


def test_consent_only_when_approved_and_keeps_first_time(db: Session):
    _, klass = _setup(db)
    waiting_student = make_student(db, "W")
    enroll(db, klass, waiting_student, "W", EnrollmentStatus.PENDING)
    assert _error(consent, db, waiting_student, klass.seq) == ErrorCode.FORBIDDEN
    student = make_student(db, "A")
    enroll(db, klass, student, "A")
    first = consent(db, student, klass.seq).consented_at
    assert first is not None
    assert consent(db, student, klass.seq).consented_at == first


def test_my_enrollment_and_classes(db: Session):
    teacher = make_teacher(db)
    k1, k2, k3 = (make_class(db, teacher, code=c) for c in ("TG-1001", "TG-1002", "TG-1003"))
    student = make_student(db, "A")
    enroll(db, k1, student, "A")
    enroll(db, k2, student, "A", EnrollmentStatus.PENDING)
    enroll(db, k3, student, "A", EnrollmentStatus.REMOVED)
    assert my_enrollment(db, student, k2.seq).status == EnrollmentStatus.PENDING
    assert _error(my_enrollment, db, make_student(db, "B"), k1.seq) == ErrorCode.NOT_FOUND
    assert {v.klass.seq for v in my_classes(db, student)} == {k1.seq, k2.seq}
