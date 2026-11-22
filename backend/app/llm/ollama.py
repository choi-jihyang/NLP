import re

import httpx

from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn

_ROLE = {"student": "user", "assistant": "assistant"}
# think 옵션을 모르는 옛 Ollama 는 생각 과정을 <think> 태그로 본문에 섞어 보낸다 → 학생에게 가기 전에 지운다
_THINK_RE = re.compile(r"<think>.*?(?:</think>|$)\s*", re.S)


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
            # Qwen3 등은 기본으로 답 전에 생각 과정을 만든다. 느리고 정답이 섞일 수 있어 끈다.
            # 생각 기능이 없는 모델(qwen2.5 등)은 이 값을 무시한다.
            "think": False,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": _ROLE[m.role], "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            res = await client.post(self._url, json=payload)
            res.raise_for_status()
        return _THINK_RE.sub("", res.json()["message"]["content"]).strip()
