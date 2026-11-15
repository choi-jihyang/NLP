from typing import Literal

from pydantic import BaseModel


class ChatTurn(BaseModel):
    """대화 한 턴. 분류기와 LLM Provider가 공통으로 쓰는 형식."""

    role: Literal["student", "assistant"]
    content: str
