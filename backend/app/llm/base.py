from abc import ABC, abstractmethod

from app.schemas.chat import ChatTurn


class LLMProvider(ABC):
    """LLM 호출 추상화. 모델을 바꿀 때는 이 인터페이스의 구현만 추가한다."""

    name: str

    @abstractmethod
    async def generate(self, system_prompt: str, messages: list[ChatTurn]) -> str:
        """시스템 프롬프트와 대화(오래된 순, 마지막이 학생의 새 메시지)를 받아 답변 텍스트를 돌려준다."""
