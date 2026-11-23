"""학생용 과제 조회. 승인된 참여 + 배포된 과제만(I7), 🔒 값 없이(I8)."""

from sqlalchemy.orm import Session

from app.core.enums import QuestionType
from app.core.errors import AppError, ErrorCode
from app.models import Assignment, Question, User
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AnswerKey
from app.schemas.student_assignments import (
    HINT_MODE_LABEL,
    MAX_HINT_STEPS,
    StudentAssignment,
    StudentQuestion,
    StudentTest,
)
from app.services.access import active_enrollment
from app.services.assignment_service import questions_of


def published_for_student(db: Session, student: User, assignment_id: int) -> Assignment:
    """초안 · 없는 과제도 FORBIDDEN — 과제가 있는지조차 알리지 않는다(④ 설계 A7)."""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.published_at is None:
        raise AppError(ErrorCode.FORBIDDEN)
    active_enrollment(db, student, assignment.class_id)
    return assignment


def _question(question: Question) -> StudentQuestion:
    hidden_count = len(AnswerKey.model_validate(question.answer_key).hidden_tests)
    return StudentQuestion(
        seq=question.seq, type=question.type, points=question.points, prompt=question.prompt, code=question.code,
        choices=list(question.choices), starter_code=question.starter_code, ai_help=question.ai_help,
        ai_enabled=question.ai_help if question.type == QuestionType.PROJECT else True,
        public_tests=[StudentTest(**t) for t in question.public_tests], hidden_test_count=hidden_count,
    )


def student_assignment(db: Session, student: User, assignment_id: int) -> StudentAssignment:
    assignment = published_for_student(db, student, assignment_id)
    policy = AiPolicy.model_validate(assignment.policy)
    return StudentAssignment(
        seq=assignment.seq, title=assignment.title, course=assignment.course, language=assignment.language,
        due_at=assignment.due_at, hint_mode=policy.hint_mode, hint_mode_label=HINT_MODE_LABEL[policy.hint_mode],
        max_hint_steps=MAX_HINT_STEPS[policy.hint_mode], external_signal_enabled=policy.external_signal_enabled,
        questions=[_question(q) for q in questions_of(db, assignment.seq)],
    )
