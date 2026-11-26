"""이해 확인 · 내 리포트(학생) · 반 리포트 · 학생별 기록(교수자). I7: 자기 것 · 자기 클래스만."""

from fastapi import APIRouter

from app.api.deps import DbSession, StudentUser, TeacherUser
from app.schemas.reports import (
    AssignmentReport,
    CheckReceipt,
    CheckSubmission,
    MyReport,
    MyReportPending,
    StudentRecord,
    UnderstandingCheckOut,
)
from app.services import report_service as svc

router = APIRouter(tags=["reports"])


@router.get("/assignments/{assignment_id}/understanding-check")
def get_understanding_check(assignment_id: int, student: StudentUser, db: DbSession) -> UnderstandingCheckOut:
    return svc.get_check(db, student, assignment_id)


@router.post("/assignments/{assignment_id}/understanding-check")
def submit_understanding_check(
    assignment_id: int, body: CheckSubmission, student: StudentUser, db: DbSession
) -> CheckReceipt:
    return svc.submit_check(db, student, assignment_id, body)


@router.get("/assignments/{assignment_id}/my-report")
def get_my_report(assignment_id: int, student: StudentUser, db: DbSession) -> MyReport | MyReportPending:
    return svc.my_report(db, student, assignment_id)


@router.get("/assignments/{assignment_id}/report")
def get_assignment_report(assignment_id: int, teacher: TeacherUser, db: DbSession) -> AssignmentReport:
    return svc.assignment_report(db, teacher, assignment_id)


@router.get("/assignments/{assignment_id}/students/{student_id}/record")
def get_student_record(assignment_id: int, student_id: int, teacher: TeacherUser, db: DbSession) -> StudentRecord:
    return svc.student_record(db, teacher, assignment_id, student_id)
