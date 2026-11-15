import httpx

from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn

_ROLE = {"student": "user", "assistant": "assistant"}


class OllamaProvider(LLMProvider):
    """로컬 Ollama 서버의 /api/chat 호출 (LLM_PROVIDER=ollama)."""

    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 120.0):
        self._url = base_url.rstrip("/") + "/api/chat"
        self._model = model
        self._timeout = timeout

    async def generate(self, system_prompt: str, messages: list[ChatTurn]) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": _ROLE[m.role], "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            res = await client.post(self._url, json=payload)
            res.raise_for_status()
        return res.json()["message"]["content"]
