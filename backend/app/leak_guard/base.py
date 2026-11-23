"""누출 검사 인터페이스. NLP 팀과의 계약은 docs/spec/integration-contract.md §4 와 같아야 한다."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.schemas.chat import ChatTurn


class LeakCheckResult(BaseModel):
    leaked: bool
    """정답·완성 코드가 들어 있어 학생에게 보내면 안 되는가"""
    reasons: list[str] = []
    """걸린 규칙 이름 (complete_function · filled_blank · code_chunk · answer_expression · accumulated)"""


class LeakGuard(ABC):
    @abstractmethod
    async def check(self, reply: str, history: list[ChatTurn]) -> LeakCheckResult:
        """LLM 답변 초안과 이전 대화(오래된 순)를 받아 누출 여부를 판정한다."""
