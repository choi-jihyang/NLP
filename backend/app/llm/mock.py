from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn


class MockProvider(LLMProvider):
    """개발용 고정 응답. 모델 없이 화면·흐름을 만들 때 사용한다."""

    name = "mock"

    DEFAULT_REPLY = "[Mock 응답] 지금까지 풀어 본 과정을 보여 주면, 다음 한 단계를 함께 생각해 볼게요."

    def __init__(self, reply: str = DEFAULT_REPLY):
        self.reply = reply
        self.calls: list[tuple[str, list[ChatTurn]]] = []
        """테스트에서 어떤 프롬프트로 호출됐는지 확인하는 용도"""

    async def generate(self, system_prompt: str, messages: list[ChatTurn]) -> str:
        self.calls.append((system_prompt, list(messages)))
        return self.reply
