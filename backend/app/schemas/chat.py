from typing import Literal

from pydantic import BaseModel


class ChatTurn(BaseModel):
    """대화 한 턴. 분류기와 LLM Provider가 공통으로 쓰는 형식."""

    role: Literal["student", "assistant"]
    content: str


# ---------- 채팅 API (api-contract "학습 AI 채팅") ----------

from datetime import datetime  # noqa: E402

from pydantic import ConfigDict, Field  # noqa: E402

from app.core.enums import ChatRole, HelpChoice, PasteField, ResponseMode  # noqa: E402


class ChatTrace(BaseModel):
    """판별 과정. DEMO_TRACE=true일 때만 채운다(결정 F)."""

    classification: str
    attempt: bool
    leak_blocked: bool
    blocked_draft: str | None
    external_signals: list[str] = []


class ChatTurnOut(BaseModel):
    role: ChatRole
    text: str
    response_mode: ResponseMode | None
    trace: ChatTrace | None = None


class ChatState(BaseModel):
    question_id: int
    turns: list[ChatTurnOut]
    hint_step: int
    max_hint_steps: int
    usage_remaining: int


class ChatBody(BaseModel):
    """붙여넣기 여부는 받지 않는다 — /paste-events(field = CHAT)로만 (I5)."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(default="", max_length=5_000)
    choice: HelpChoice | None = None


class PasteBody(BaseModel):
    """내용 필드 없음. 알 수 없는 필드(content 등)는 거부한다(I5)."""

    model_config = ConfigDict(extra="forbid")

    question_id: int
    field: PasteField
    length: int = Field(ge=0, le=1_000_000)
    pasted_at: datetime


class OkOut(BaseModel):
    ok: bool = True
