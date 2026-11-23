"""교수자: 과제 목록 · 빈 초안 · 저장 · 조회 · 수정 · 배포 · 결과 공개 (④ 설계)."""

from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.schemas.assignments import AssignmentData, AssignmentSummary, DraftBody, PublishOut, ReleaseOut
from app.services import assignment_service as svc

router = APIRouter(tags=["assignments"])


@router.get("/classes/{class_id}/assignments")
def list_assignments(class_id: int, teacher: TeacherUser, db: DbSession) -> list[AssignmentSummary]:
    return svc.list_summaries(db, teacher, class_id)


@router.post("/classes/{class_id}/assignments/drafts")
def create_draft(class_id: int, body: DraftBody, teacher: TeacherUser, db: DbSession) -> AssignmentData:
    return svc.new_blank_draft(db, teacher, class_id)


@router.post("/classes/{class_id}/assignments", status_code=201)
def create_assignment(class_id: int, body: AssignmentData, teacher: TeacherUser, db: DbSession) -> AssignmentData:
    return svc.assignment_data(db, svc.create_assignment(db, teacher, class_id, body))


@router.get("/assignments/{assignment_id}")
def get_assignment(assignment_id: int, teacher: TeacherUser, db: DbSession) -> AssignmentData:
    return svc.assignment_data(db, svc.get_owned(db, teacher, assignment_id))


@router.put("/assignments/{assignment_id}")
def update_assignment(assignment_id: int, body: AssignmentData, teacher: TeacherUser, db: DbSession) -> AssignmentData:
    return svc.assignment_data(db, svc.update_assignment(db, teacher, assignment_id, body))


@router.post("/assignments/{assignment_id}/publish")
def publish_assignment(assignment_id: int, teacher: TeacherUser, db: DbSession) -> PublishOut:
    return PublishOut(invite_code=svc.publish(db, teacher, assignment_id))


@router.post("/assignments/{assignment_id}/release")
def release_results(assignment_id: int, teacher: TeacherUser, db: DbSession) -> ReleaseOut:
    svc.release(db, teacher, assignment_id)
    return ReleaseOut()
