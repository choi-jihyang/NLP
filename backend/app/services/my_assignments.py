"""학생 "내 과제" 목록 (/me/classes의 assignments). 결과 공개 전에는 점수를 넣지 않는다."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AnswerStatus, EnrollmentStatus
from app.models import Answer, Assignment, Enrollment, Question, Submission
from app.schemas.ai_policy import AiPolicy
from app.schemas.enrollments import MyAssignmentOut
from app.schemas.student_assignments import HINT_MODE_LABEL


def my_assignments(db: Session, enrollment: Enrollment) -> list[MyAssignmentOut]:
    if enrollment.status != EnrollmentStatus.APPROVED:
        return []
    assignments = db.scalars(
        select(Assignment).where(Assignment.class_id == enrollment.class_id, Assignment.published_at.is_not(None))
        .order_by(Assignment.seq.desc())
    )
    out = []
    for a in assignments:
        policy = AiPolicy.model_validate(a.policy)
        total = db.scalar(select(func.count()).select_from(Question).where(Question.assignment_id == a.seq)) or 0
        sub = db.scalar(select(Submission).where(Submission.assignment_id == a.seq,
                                                 Submission.enrollment_id == enrollment.seq))
        answers = list(db.scalars(select(Answer).where(Answer.submission_id == sub.seq))) if sub else []
        released = a.results_released_at is not None
        status = "RELEASED" if released else ("FINALIZED" if sub and sub.finalized_at else "IN_PROGRESS")
        score_text = None
        if released:
            points = sum(db.scalars(select(Question.points).where(Question.assignment_id == a.seq)))
            pending = any(x.score is None and x.status is AnswerStatus.SUBMITTED for x in answers)
            score_text = f"{sum(x.score or 0 for x in answers)}/{points}점" + (" (채점 중 포함)" if pending else "")
        out.append(MyAssignmentOut(
            seq=a.seq, title=a.title, language=a.language.value, status=status, due_at=a.due_at,
            hint_mode=policy.hint_mode.value, hint_mode_label=HINT_MODE_LABEL[policy.hint_mode],
            submitted=sum(x.status is AnswerStatus.SUBMITTED for x in answers), total=total, score_text=score_text,
        ))
    return out
