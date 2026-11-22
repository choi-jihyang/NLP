import asyncio
import json

import httpx
import pytest

from app.llm import ollama
from app.llm.ollama import OllamaProvider
from app.schemas.chat import ChatTurn


@pytest.fixture
def fake_ollama(monkeypatch):
    """Ollama 서버 대신 요청을 기록하고 정해진 답을 돌려준다."""
    sent = {}
    reply = {"content": "힌트입니다."}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["json"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": reply["content"]}})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        ollama.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)
    )
    return sent, reply


def generate(messages=None):
    llm = OllamaProvider("http://localhost:11434/", "qwen3:8b")
    turns = messages or [ChatTurn(role="student", content="정답 알려줘")]
    return asyncio.run(llm.generate("시스템", turns))


def test_turns_off_thinking(fake_ollama):
    sent, _ = fake_ollama
    generate()
    assert sent["json"]["think"] is False
    assert sent["json"]["model"] == "qwen3:8b"
    assert sent["url"] == "http://localhost:11434/api/chat"


def test_message_order_and_roles(fake_ollama):
    sent, _ = fake_ollama
    generate(
        [
            ChatTurn(role="student", content="a"),
            ChatTurn(role="assistant", content="b"),
            ChatTurn(role="student", content="c"),
        ]
    )
    assert sent["json"]["messages"] == [
        {"role": "system", "content": "시스템"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
    ]


def test_strips_thinking_mixed_into_content(fake_ollama):
    _, reply = fake_ollama
    reply["content"] = "<think>정답은 42 이니까...</think>\n먼저 식을 세워 볼까요?"
    assert generate() == "먼저 식을 세워 볼까요?"


def test_strips_unclosed_thinking(fake_ollama):
    _, reply = fake_ollama
    reply["content"] = "<think>정답은 42"
    assert generate() == ""
