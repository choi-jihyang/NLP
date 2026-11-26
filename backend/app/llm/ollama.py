import re

import httpx

from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn

_ROLE = {"student": "user", "assistant": "assistant"}
# think 옵션을 모르는 옛 Ollama 는 생각 과정을 본문 맨 앞에 <think>…</think> 로 섞어 보낸다 → 학생에게 가기 전에 지운다.
# 닫는 태그가 없으면 끝까지 지우는 규칙은 맨 앞에서만 쓴다(답 중간에 나온 "<think>" 글자 뒤를 날리지 않도록).
_LEADING_THINK_RE = re.compile(r"^\s*<\s*think\s*>.*?(?:<\s*/\s*think\s*>|$)", re.S | re.I)
# 학생 유도로 짝 없는 </think> 만 반복해 내는 경우가 있다 → 위치와 상관없이 태그 자체는 지운다
_THINK_TAG_RE = re.compile(r"<\s*/?\s*think\s*>", re.I)


def strip_thinking(text: str) -> str:
    """생각 과정과 남은 think 태그를 지운다. 지운 결과가 비면 빈 문자열(대체 문구는 chat_service 가 정한다)."""
    return _THINK_TAG_RE.sub("", _LEADING_THINK_RE.sub("", text, count=1)).strip()


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
        return strip_thinking(res.json()["message"]["content"])
