"""교수자 과제: 빈 초안 · 저장 · 조회 · 수정(배포 후 문항 잠금) · 배포 · 결과 공개 · 목록 (④ 설계 A3 · A4)."""

from collections import Counter
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import Language, QuestionType
from app.core.errors import AppError, ErrorCode
from app.models import Assignment, ClassRoom, Question, Submission, User
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AssignmentData, AssignmentSummary
from app.services import assignment_md
from app.services.access import approved_count, own_class
from app.services.question_codec import same_questions, to_columns, to_data

TYPE_LABEL = {
    QuestionType.MULTIPLE_CHOICE: "객관식",
    QuestionType.SHORT_ANSWER: "출력 예측",
    QuestionType.CODE: "코드 작성",
    QuestionType.PROJECT: "간단 제작",
}


def new_blank_draft(db: Session, teacher: User, class_id: int) -> AssignmentData:
    """저장하지 않은 빈 초안. AI 정책은 클래스 기본값."""
    klass = own_class(db, teacher, class_id)
    return AssignmentData(
        class_id=klass.seq, title="새 과제", language=Language.C, policy=AiPolicy.model_validate(klass.ai_defaults)
    )


def new_sample_draft(db: Session, teacher: User, class_id: int) -> AssignmentData:
    """샘플 md(C 2진수 과제)를 읽은 초안. AI 정책은 클래스 기본값."""
    klass = own_class(db, teacher, class_id)
    return assignment_md.parse(assignment_md.sample_text(), AiPolicy.model_validate(klass.ai_defaults), klass.seq)


def extract_draft(db: Session, teacher: User, class_id: int, filename: str, raw: bytes) -> AssignmentData:
    """올린 md 과제 파일 → 저장 전 초안. 양식 오류는 줄마다 모아 VALIDATION_FAILED 메시지로."""
    klass = own_class(db, teacher, class_id)
    try:
        if not filename.lower().endswith((".md", ".markdown", ".txt")):
            raise assignment_md.MdFormatError([".md 파일만 올릴 수 있어요 (PDF는 아직 지원하지 않아요)"])
        return assignment_md.parse(
            assignment_md.decode(raw), AiPolicy.model_validate(klass.ai_defaults), klass.seq
        )
    except assignment_md.MdFormatError as exc:
        raise AppError(ErrorCode.VALIDATION_FAILED, "과제 파일 양식이 맞지 않아요.\n" + str(exc)) from exc


def get_owned(db: Session, teacher: User, assignment_id: int) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise AppError(ErrorCode.NOT_FOUND)
    own_class(db, teacher, assignment.class_id)
    return assignment


def questions_of(db: Session, assignment_id: int) -> list[Question]:
    query = select(Question).where(Question.assignment_id == assignment_id).order_by(Question.position)
    return list(db.scalars(query))


def assignment_data(db: Session, assignment: Assignment) -> AssignmentData:
    return AssignmentData(
        seq=assignment.seq, class_id=assignment.class_id, title=assignment.title, course=assignment.course,
        audience=assignment.audience, language=assignment.language, description=assignment.description,
        due_at=assignment.due_at, published=assignment.published_at is not None,
        results_released=assignment.results_released_at is not None,
        policy=AiPolicy.model_validate(assignment.policy),
        questions=[to_data(q) for q in questions_of(db, assignment.seq)],
    )


def _info(data: AssignmentData) -> dict[str, Any]:
    return {
        "title": data.title, "course": data.course, "audience": data.audience, "language": data.language,
        "description": data.description, "due_at": data.due_at, "policy": data.policy.model_dump(mode="json"),
    }


def _replace_questions(db: Session, assignment: Assignment, data: AssignmentData) -> None:
    """배포 전에만: 문항을 통째로 바꾼다(학생 답이 아직 없음)."""
    db.execute(delete(Question).where(Question.assignment_id == assignment.seq))
    for position, question in enumerate(data.questions):
        db.add(Question(assignment_id=assignment.seq, **to_columns(question, position)))


def create_assignment(db: Session, teacher: User, class_id: int, data: AssignmentData) -> Assignment:
    klass = own_class(db, teacher, class_id)
    assignment = Assignment(class_id=klass.seq, **_info(data))
    db.add(assignment)
    db.flush()
    _replace_questions(db, assignment, data)
    db.commit()
    return assignment


def update_assignment(db: Session, teacher: User, assignment_id: int, data: AssignmentData) -> Assignment:
    assignment = get_owned(db, teacher, assignment_id)
    if assignment.results_released_at is not None:
        raise AppError(ErrorCode.CONFLICT, "결과를 공개한 과제는 고칠 수 없습니다.")
    if assignment.published_at is not None:
        unchanged = data.language == assignment.language and same_questions(questions_of(db, assignment.seq),
                                                                             data.questions)
        if not unchanged:
            raise AppError(ErrorCode.CONFLICT, "배포한 과제는 문항과 언어를 고칠 수 없습니다.")
    for name, value in _info(data).items():
        setattr(assignment, name, value)
    if assignment.published_at is None:
        _replace_questions(db, assignment, data)
    db.commit()
    return assignment


def publish(db: Session, teacher: User, assignment_id: int) -> str:
    """배포하고 학생에게 알려 줄 수업 코드를 돌려준다. 이미 배포했으면 그대로."""
    assignment = get_owned(db, teacher, assignment_id)
    if not questions_of(db, assignment.seq):
        raise AppError(ErrorCode.CONFLICT, "문항이 없는 과제는 배포할 수 없습니다.")
    if assignment.published_at is None:
        assignment.published_at = now_kst()
        db.commit()
    klass = db.get(ClassRoom, assignment.class_id)
    assert klass is not None
    return klass.invite_code


def release(db: Session, teacher: User, assignment_id: int) -> None:
    assignment = get_owned(db, teacher, assignment_id)
    if assignment.published_at is None:
        raise AppError(ErrorCode.CONFLICT, "배포하지 않은 과제는 결과를 공개할 수 없습니다.")
    if assignment.results_released_at is None:
        assignment.results_released_at = now_kst()
        db.commit()


def _status(assignment: Assignment) -> str:
    if assignment.published_at is None:
        return "DRAFT"
    if assignment.due_at is not None and assignment.due_at <= now_kst():
        return "CLOSED"
    return "OPEN"


def _kinds(questions: list[Question]) -> str:
    counts = Counter(q.type for q in questions)
    return " · ".join(f"{label} {counts[t]}" for t, label in TYPE_LABEL.items() if counts[t])


def _finalized_count(db: Session, assignment_id: int) -> int:
    query = select(func.count()).select_from(Submission).where(
        Submission.assignment_id == assignment_id, Submission.finalized_at.is_not(None)
    )
    return db.scalar(query) or 0


def list_summaries(db: Session, teacher: User, class_id: int) -> list[AssignmentSummary]:
    klass = own_class(db, teacher, class_id)
    students = approved_count(db, klass.seq)
    assignments = db.scalars(
        select(Assignment).where(Assignment.class_id == klass.seq).order_by(Assignment.seq.desc())
    )
    return [
        AssignmentSummary(
            seq=a.seq, title=a.title, kinds=_kinds(questions_of(db, a.seq)), status=_status(a), due_at=a.due_at,
            hint_mode=AiPolicy.model_validate(a.policy).hint_mode, student_count=students,
            submitted_count=_finalized_count(db, a.seq), results_released=a.results_released_at is not None,
        )
        for a in assignments
    ]
