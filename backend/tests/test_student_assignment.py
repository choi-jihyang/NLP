import pytest
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus
from app.core.errors import AppError, ErrorCode
from app.schemas.assignments import AssignmentData
from app.schemas.student_assignments import StudentAssignment
from app.services.assignment_service import create_assignment, publish
from app.services.student_assignment_service import student_assignment
from tests.factories import enroll, make_class, make_student, make_teacher

CODE = {
    "type": "CODE", "points": 20, "prompt": "변환기",
    "tests": [{"input": "5", "expected_output": "101"}, {"input": "8", "expected_output": "1000", "hidden": True}],
}
PROJECT_OFF = {"type": "PROJECT", "points": 35, "prompt": "뺄셈기", "rubric": ["음수"], "ai_help": False}
PROJECT_ON = {**PROJECT_OFF, "ai_help": True}


def _setup(db: Session, publish_it: bool = True, hint_mode: str = "STEP"):  # noqa: ANN202
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    data = AssignmentData.model_validate({
        "title": "2진수", "language": "C", "policy": {"hint_mode": hint_mode},
        "questions": [CODE, PROJECT_OFF, PROJECT_ON],
    })
    assignment = create_assignment(db, teacher, klass.seq, data)
    if publish_it:
        publish(db, teacher, assignment.seq)
    return teacher, klass, assignment


def _error(db: Session, student, assignment_id: int) -> ErrorCode:  # noqa: ANN001
    with pytest.raises(AppError) as info:
        student_assignment(db, student, assignment_id)
    return info.value.code


def test_approved_student_sees_published_assignment(db: Session):
    _, klass, assignment = _setup(db)
    student = make_student(db)
    enroll(db, klass, student, "20260001")
    view = student_assignment(db, student, assignment.seq)
    assert isinstance(view, StudentAssignment)
    assert (view.hint_mode, view.hint_mode_label, view.max_hint_steps) == ("STEP", "한 단계씩", 3)
    code, off, on = view.questions
    assert [t.model_dump() for t in code.public_tests] == [{"input": "5", "expected_output": "101"}]
    assert code.hidden_test_count == 1 and code.ai_enabled is True
    assert (off.ai_enabled, on.ai_enabled) == (False, True)


@pytest.mark.parametrize(("mode", "label", "steps"), [
    ("NONE", "힌트 없음", 0), ("CONCEPT", "개념만", 1), ("EARNED", "시도한 만큼 열기", 3),
])
def test_hint_labels(db: Session, mode: str, label: str, steps: int):
    _, klass, assignment = _setup(db, hint_mode=mode)
    student = make_student(db)
    enroll(db, klass, student, "20260001")
    view = student_assignment(db, student, assignment.seq)
    assert (view.hint_mode_label, view.max_hint_steps) == (label, steps)


@pytest.mark.parametrize("status", [EnrollmentStatus.PENDING, EnrollmentStatus.REMOVED, EnrollmentStatus.REJECTED])
def test_inactive_student_is_forbidden(db: Session, status: EnrollmentStatus):
    _, klass, assignment = _setup(db)
    student = make_student(db)
    enroll(db, klass, student, "20260001", status)
    assert _error(db, student, assignment.seq) == ErrorCode.FORBIDDEN


def test_student_of_other_class_is_forbidden(db: Session):
    teacher, _, assignment = _setup(db)
    other_class = make_class(db, teacher, code="TG-2000")
    student = make_student(db)
    enroll(db, other_class, student, "20260001")
    assert _error(db, student, assignment.seq) == ErrorCode.FORBIDDEN


def test_draft_and_missing_assignment_are_forbidden(db: Session):
    _, klass, draft = _setup(db, publish_it=False)
    student = make_student(db)
    enroll(db, klass, student, "20260001")
    assert _error(db, student, draft.seq) == ErrorCode.FORBIDDEN
    assert _error(db, student, 999) == ErrorCode.FORBIDDEN


def test_student_schema_has_no_locked_fields():
    locked = {"answer", "accepted_answers", "misconceptions", "rubric", "model_answer", "variant", "tests",
              "hidden_tests", "answer_key"}
    from app.schemas.student_assignments import StudentQuestion

    assert not locked & set(StudentQuestion.model_fields)
    assert not locked & set(StudentAssignment.model_fields)
