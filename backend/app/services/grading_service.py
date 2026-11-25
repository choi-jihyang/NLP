"""교수자: 간단 제작 답안 목록 · 채점. 결과 공개 뒤에도 채점할 수 있다(api-contract 결정 D)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import AnswerStatus, PasteField, QuestionType
from app.core.errors import AppError, ErrorCode
from app.models import Answer, Enrollment, PasteEvent, Question, Submission, User
from app.schemas.assignments import AnswerKey
from app.schemas.grading import GradingItem
from app.services.assignment_service import get_owned, questions_of

LONG_PASTE = 200
"""답 칸에 이 글자 수 이상 붙여넣으면 참고 신호로 보여 준다"""


def signals(db: Session, answer: Answer) -> list[str]:
    """외부 AI 참고 신호 — 붙여넣기 길이 · 시점만으로 계산한다(내용은 저장하지 않음, I5). 판정이 아니다."""
    events = db.scalars(select(PasteEvent).where(PasteEvent.answer_id == answer.seq)).all()
    out = []
    long_answer = [e for e in events if e.field is PasteField.ANSWER and e.length >= LONG_PASTE]
    if long_answer:
        out.append(f"답 칸에 {max(e.length for e in long_answer)}자를 한 번에 붙여넣음")
    if any(e.field is PasteField.CONCEPT_CHECK for e in events):
        out.append("개념 확인 답변을 붙여넣음")
    return out


def _item(db: Session, answer: Answer, q: Question, index: int, student_no: str) -> GradingItem:
    return GradingItem(
        answer_id=answer.seq, student_name=student_no, question_index=index, points=q.points,
        rubric=AnswerKey.model_validate(q.answer_key).rubric, content=answer.content,
        signals=signals(db, answer), score=answer.score, feedback=answer.feedback or "",
    )


def grading_list(db: Session, teacher: User, assignment_id: int) -> list[GradingItem]:
    assignment = get_owned(db, teacher, assignment_id)
    projects = {q.seq: (i, q) for i, q in enumerate(questions_of(db, assignment.seq), start=1)
                if q.type is QuestionType.PROJECT}
    if not projects:
        return []
    rows = db.execute(
        select(Answer, Enrollment.student_no)
        .join(Submission, Answer.submission_id == Submission.seq)
        .join(Enrollment, Submission.enrollment_id == Enrollment.seq)
        .where(Submission.assignment_id == assignment.seq, Answer.question_id.in_(projects),
               Answer.status == AnswerStatus.SUBMITTED)
        .order_by(Enrollment.student_no, Answer.question_id)
    ).all()
    return [_item(db, a, projects[a.question_id][1], projects[a.question_id][0], no) for a, no in rows]


def grade(db: Session, teacher: User, answer_id: int, score: int, feedback: str) -> GradingItem:
    answer = db.get(Answer, answer_id)
    if answer is None:
        raise AppError(ErrorCode.NOT_FOUND)
    sub = db.get(Submission, answer.submission_id)
    assert sub is not None
    assignment = get_owned(db, teacher, sub.assignment_id)  # 남의 클래스면 FORBIDDEN
    q = db.get(Question, answer.question_id)
    assert q is not None
    if q.type is not QuestionType.PROJECT:
        raise AppError(ErrorCode.CONFLICT, "간단 제작 문항만 직접 채점합니다.")
    if answer.status is not AnswerStatus.SUBMITTED:
        raise AppError(ErrorCode.CONFLICT, "아직 제출하지 않은 답안입니다.")
    if score > q.points:
        raise AppError(ErrorCode.VALIDATION_FAILED, f"점수는 0–{q.points}점이어야 합니다.")
    answer.score, answer.feedback = score, feedback
    answer.graded_by, answer.graded_at = teacher.seq, now_kst()
    db.commit()
    index = next(i for i, x in enumerate(questions_of(db, assignment.seq), start=1) if x.seq == q.seq)
    enrollment = db.get(Enrollment, sub.enrollment_id)
    assert enrollment is not None
    return _item(db, answer, q, index, enrollment.student_no)
