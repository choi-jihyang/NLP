"""학생 입장(토큰 선택) · 참여 상태 · 기록 동의."""

from fastapi import APIRouter

from app.api.deps import DbSession, OptionalUser, StudentUser
from app.schemas.enrollments import JoinBody, JoinOut, OkOut, ReentryBody, ReentryOut, StatusOut
from app.services import enrollment_service, join_service

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("")
def join_class(body: JoinBody, caller: OptionalUser, db: DbSession) -> JoinOut:
    result = join_service.join(db, body.invite_code, body.student_no, caller)
    return JoinOut(
        class_id=result.klass.seq, class_name=result.klass.name, status=result.status,
        access_token=result.access_token, reentry_ticket=result.reentry_ticket,
    )


@router.post("/reentry")
def claim_reentry(body: ReentryBody, db: DbSession) -> ReentryOut:
    """다시 입장 티켓으로 토큰 받기. 교수자 수락 전이면 PENDING."""
    result = join_service.claim_reentry(db, body.ticket)
    return ReentryOut(status=result.status, access_token=result.access_token)


@router.get("/{class_id}/me")
def my_status(class_id: int, student: StudentUser, db: DbSession) -> StatusOut:
    return StatusOut(status=enrollment_service.my_enrollment(db, student, class_id).status)


@router.post("/{class_id}/consent")
def accept_consent(class_id: int, student: StudentUser, db: DbSession) -> OkOut:
    enrollment_service.consent(db, student, class_id)
    return OkOut()
