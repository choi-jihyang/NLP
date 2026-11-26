"""학생: 배포된 과제를 정답 없이 조회 (I7 · I8)."""

from fastapi import APIRouter

from app.api.deps import DbSession, StudentUser
from app.schemas.student_assignments import StudentAssignment
from app.services.student_assignment_service import student_assignment

router = APIRouter(tags=["solve"])


@router.get("/assignments/{assignment_id}/solve")
def get_student_assignment(assignment_id: int, student: StudentUser, db: DbSession) -> StudentAssignment:
    return student_assignment(db, student, assignment_id)
