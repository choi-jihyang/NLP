"""교수자: 과제 목록 · 빈 초안 · 저장 · 조회 · 수정 · 배포 · 결과 공개 (④ 설계)."""

from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.classifier import get_classifier
from app.core.config import get_settings
from app.leak_guard import get_leak_guard
from app.llm import get_llm_provider
from app.schemas.assignments import AssignmentData, AssignmentSummary, DraftBody, PublishOut, ReleaseOut
from app.services import assignment_service as svc
from app.services.simulate_service import SimulationCase, simulate

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


@router.post("/assignments/simulate")
async def simulate_attacks(body: AssignmentData, teacher: TeacherUser) -> list[SimulationCase]:
    """저장 전 초안으로 우회 요청을 실제 정책 경로(분류기 · LLM · 누출 검사)에 보내 본다."""
    return await simulate(body, get_classifier(), get_llm_provider(), get_leak_guard(),
                          get_settings().classifier_min_confidence)


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
