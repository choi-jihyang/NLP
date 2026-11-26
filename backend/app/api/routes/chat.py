"""학생: 문항별 AI 채팅 · 붙여넣기 기록 (⑥, I1 · I5 · I6 · I7)."""

from fastapi import APIRouter

from app.api.deps import DbSession, StudentUser
from app.classifier import get_classifier
from app.leak_guard import get_leak_guard
from app.llm import get_llm_provider
from app.schemas.chat import ChatBody, ChatState, OkOut, PasteBody
from app.services import chat_api_service as svc

router = APIRouter(tags=["chat"])


@router.get("/assignments/{assignment_id}/questions/{question_id}/chat")
def get_chat(assignment_id: int, question_id: int, student: StudentUser, db: DbSession) -> ChatState:
    return svc.get_chat(db, student, assignment_id, question_id)


@router.post("/assignments/{assignment_id}/questions/{question_id}/chat")
async def send_chat(
    assignment_id: int, question_id: int, body: ChatBody, student: StudentUser, db: DbSession
) -> ChatState:
    return await svc.send_chat(
        db, student, assignment_id, question_id, body.message, body.choice,
        get_classifier(), get_llm_provider(), get_leak_guard(),
    )  # fmt: skip


@router.post("/paste-events")
def log_paste(body: PasteBody, student: StudentUser, db: DbSession) -> OkOut:
    svc.log_paste(db, student, body)
    return OkOut()
