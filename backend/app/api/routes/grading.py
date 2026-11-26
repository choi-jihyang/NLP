"""교수자: 간단 제작 채점 (I7: 자기 클래스만)."""

from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.schemas.grading import GradeBody, GradingItem
from app.services import grading_service as svc

router = APIRouter(tags=["grading"])


@router.get("/assignments/{assignment_id}/grading")
def grading_list(assignment_id: int, teacher: TeacherUser, db: DbSession) -> list[GradingItem]:
    return svc.grading_list(db, teacher, assignment_id)


@router.put("/answers/{answer_id}/grade")
def grade_answer(answer_id: int, body: GradeBody, teacher: TeacherUser, db: DbSession) -> GradingItem:
    return svc.grade(db, teacher, answer_id, body.score, body.feedback)
