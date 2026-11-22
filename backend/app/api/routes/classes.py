"""교수자: 클래스 · AI 기본값 · 명단 · 참여 요청 · 학생."""

from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.core.enums import JoinMode
from app.models import ClassMember
from app.schemas.ai_policy import AiPolicy
from app.schemas.classes import ClassCreate, ClassInfo, RosterEntry, RosterSettings
from app.schemas.enrollments import DecisionBody, JoinRequestOut, OkOut, StatusOut, StudentOut
from app.services import class_service, enrollment_service, roster_service

router = APIRouter(prefix="/classes", tags=["classes"])


def _info(view: class_service.ClassView) -> ClassInfo:
    k = view.klass
    return ClassInfo(
        seq=k.seq, name=k.name, invite_code=k.invite_code, plan=k.plan, student_limit=k.student_limit,
        student_count=view.student_count, starts_at=k.starts_at, expires_at=k.expires_at,
    )


def _roster(join_mode: JoinMode, members: list[ClassMember]) -> RosterSettings:
    entries = [RosterEntry(student_no=m.student_no, is_use=m.is_use) for m in members]
    return RosterSettings(join_mode=join_mode, roster=entries)


@router.get("")
def list_classes(teacher: TeacherUser, db: DbSession) -> list[ClassInfo]:
    return [_info(v) for v in class_service.list_classes(db, teacher)]


@router.post("", status_code=201)
def create_class(body: ClassCreate, teacher: TeacherUser, db: DbSession) -> ClassInfo:
    klass = class_service.create_class(db, teacher, body.name, body.starts_on, body.payment_seq)
    return _info(class_service.ClassView(klass, 0))


@router.get("/{class_id}")
def get_class(class_id: int, teacher: TeacherUser, db: DbSession) -> ClassInfo:
    return _info(class_service.get_class_view(db, teacher, class_id))


@router.get("/{class_id}/ai-defaults")
def get_ai_defaults(class_id: int, teacher: TeacherUser, db: DbSession) -> AiPolicy:
    return class_service.get_ai_defaults(db, teacher, class_id)


@router.put("/{class_id}/ai-defaults")
def save_ai_defaults(class_id: int, body: AiPolicy, teacher: TeacherUser, db: DbSession) -> AiPolicy:
    return class_service.save_ai_defaults(db, teacher, class_id, body)


@router.get("/{class_id}/roster")
def get_roster(class_id: int, teacher: TeacherUser, db: DbSession) -> RosterSettings:
    return _roster(*roster_service.get_roster(db, teacher, class_id))


@router.put("/{class_id}/roster")
def save_roster(class_id: int, body: RosterSettings, teacher: TeacherUser, db: DbSession) -> RosterSettings:
    wanted = {entry.student_no: entry.is_use for entry in body.roster}
    return _roster(*roster_service.save_roster(db, teacher, class_id, body.join_mode, wanted))


@router.get("/{class_id}/join-requests")
def list_join_requests(class_id: int, teacher: TeacherUser, db: DbSession) -> list[JoinRequestOut]:
    return [
        JoinRequestOut(seq=e.seq, student_no=e.student_no, requested_at=e.updated_at,
                       is_reentry=enrollment_service.is_reentry(e))
        for e in enrollment_service.list_requests(db, teacher, class_id)
    ]


@router.post("/{class_id}/join-requests/{enrollment_seq}")
def decide_join_request(
    class_id: int, enrollment_seq: int, body: DecisionBody, teacher: TeacherUser, db: DbSession
) -> StatusOut:
    enrollment = enrollment_service.decide_request(db, teacher, class_id, enrollment_seq, body.approve)
    return StatusOut(status=enrollment.status)


@router.get("/{class_id}/students")
def list_students(class_id: int, teacher: TeacherUser, db: DbSession) -> list[StudentOut]:
    return [StudentOut(seq=e.student_id, student_no=e.student_no)
            for e in enrollment_service.list_students(db, teacher, class_id)]


@router.delete("/{class_id}/students/{student_id}")
def remove_student(class_id: int, student_id: int, teacher: TeacherUser, db: DbSession) -> OkOut:
    enrollment_service.remove_student(db, teacher, class_id, student_id)
    return OkOut()
