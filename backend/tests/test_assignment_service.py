from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus, HintMode, Language
from app.core.errors import AppError, ErrorCode
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AssignmentData
from app.services.assignment_service import (
    assignment_data,
    create_assignment,
    get_owned,
    list_summaries,
    new_blank_draft,
    publish,
    release,
    update_assignment,
)
from tests.factories import enroll, make_class, make_student, make_teacher

MC = {"type": "MULTIPLE_CHOICE", "points": 10, "prompt": "1011은?", "choices": ["11", "13"], "answer": "0"}
CODE = {
    "type": "CODE", "points": 20, "prompt": "변환기",
    "tests": [{"input": "5", "expected_output": "101"}, {"input": "8", "expected_output": "1000", "hidden": True}],
}


def _data(**changes: object) -> AssignmentData:
    return AssignmentData.model_validate({"title": "2진수", "language": "C", "questions": [MC, CODE], **changes})


def _error(fn, *args) -> ErrorCode:  # noqa: ANN001
    with pytest.raises(AppError) as info:
        fn(*args)
    return info.value.code


def _setup(db: Session):  # noqa: ANN202
    teacher = make_teacher(db)
    return teacher, make_class(db, teacher)


def test_blank_draft_uses_class_ai_defaults(db: Session):
    teacher, klass = _setup(db)
    klass.ai_defaults = AiPolicy(hint_mode=HintMode.STEP, usage_limit=7).model_dump(mode="json")
    db.commit()
    draft = new_blank_draft(db, teacher, klass.seq)
    assert (draft.seq, draft.class_id, draft.language, draft.questions) == (None, klass.seq, Language.C, [])
    assert (draft.policy.hint_mode, draft.policy.usage_limit) == (HintMode.STEP, 7)


def test_create_and_read_back_everything(db: Session):
    teacher, klass = _setup(db)
    saved = assignment_data(db, create_assignment(db, teacher, klass.seq, _data()))
    assert saved.seq and saved.class_id == klass.seq and not saved.published
    assert [q.type for q in saved.questions] == ["MULTIPLE_CHOICE", "CODE"]
    assert saved.questions[1].tests[1].hidden is True and saved.questions[0].answer == "0"


def test_draft_questions_are_replaced(db: Session):
    teacher, klass = _setup(db)
    a = create_assignment(db, teacher, klass.seq, _data())
    updated = assignment_data(db, update_assignment(db, teacher, a.seq, _data(title="새 이름", questions=[CODE])))
    assert updated.title == "새 이름" and [q.type for q in updated.questions] == ["CODE"]


def test_published_questions_are_locked(db: Session):
    teacher, klass = _setup(db)
    a = create_assignment(db, teacher, klass.seq, _data())
    publish(db, teacher, a.seq)
    assert _error(update_assignment, db, teacher, a.seq, _data(questions=[CODE, MC])) == ErrorCode.CONFLICT  # 순서
    flipped = {**CODE, "tests": [{**t, "hidden": True} for t in CODE["tests"]]}
    assert _error(update_assignment, db, teacher, a.seq, _data(questions=[MC, flipped])) == ErrorCode.CONFLICT
    assert _error(update_assignment, db, teacher, a.seq, _data(language="PYTHON")) == ErrorCode.CONFLICT


def test_published_info_and_policy_can_change_with_same_questions(db: Session):
    teacher, klass = _setup(db)
    a = create_assignment(db, teacher, klass.seq, _data())
    publish(db, teacher, a.seq)
    due = now_kst() + timedelta(days=3)
    changed = _data(title="마감 연장", due_at=due.isoformat(), policy={"usage_limit": 5})
    result = assignment_data(db, update_assignment(db, teacher, a.seq, changed))
    assert (result.title, result.due_at, result.policy.usage_limit) == ("마감 연장", due, 5)


def test_released_assignment_is_fully_locked(db: Session):
    teacher, klass = _setup(db)
    a = create_assignment(db, teacher, klass.seq, _data())
    publish(db, teacher, a.seq)
    release(db, teacher, a.seq)
    assert _error(update_assignment, db, teacher, a.seq, _data(title="바꿈")) == ErrorCode.CONFLICT


def test_publish_and_release_rules(db: Session):
    teacher, klass = _setup(db)
    empty = create_assignment(db, teacher, klass.seq, _data(questions=[]))
    assert _error(publish, db, teacher, empty.seq) == ErrorCode.CONFLICT
    a = create_assignment(db, teacher, klass.seq, _data())
    assert _error(release, db, teacher, a.seq) == ErrorCode.CONFLICT  # 배포 전
    assert publish(db, teacher, a.seq) == klass.invite_code
    first = a.published_at
    publish(db, teacher, a.seq)
    assert a.published_at == first  # 다시 배포해도 그대로
    release(db, teacher, a.seq)
    assert a.results_released_at is not None


def test_other_teacher_and_missing_assignment(db: Session):
    teacher, klass = _setup(db)
    a = create_assignment(db, teacher, klass.seq, _data())
    other = make_teacher(db, "o@x.test")
    assert _error(get_owned, db, other, a.seq) == ErrorCode.FORBIDDEN
    assert _error(create_assignment, db, other, klass.seq, _data()) == ErrorCode.FORBIDDEN
    assert _error(get_owned, db, teacher, 999) == ErrorCode.NOT_FOUND


def test_summaries_status_and_counts(db: Session):
    teacher, klass = _setup(db)
    enroll(db, klass, make_student(db, "A"), "A")
    enroll(db, klass, make_student(db, "B"), "B", EnrollmentStatus.PENDING)
    draft = create_assignment(db, teacher, klass.seq, _data(title="초안"))
    tomorrow, yesterday = (now_kst() + timedelta(days=d) for d in (1, -1))
    open_ = create_assignment(db, teacher, klass.seq, _data(title="진행", due_at=tomorrow.isoformat()))
    closed = create_assignment(db, teacher, klass.seq, _data(title="마감", due_at=yesterday.isoformat()))
    publish(db, teacher, open_.seq)
    publish(db, teacher, closed.seq)
    by_title = {s.title: s for s in list_summaries(db, teacher, klass.seq)}
    assert {t: s.status for t, s in by_title.items()} == {"초안": "DRAFT", "진행": "OPEN", "마감": "CLOSED"}
    assert by_title["초안"].kinds == "객관식 1 · 코드 작성 1"
    assert by_title["진행"].student_count == 1 and by_title["진행"].submitted_count == 0
    assert by_title["초안"].seq == draft.seq
