from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider

__all__ = ["LLMProvider", "get_llm_provider"]


@lru_cache
def get_llm_provider() -> LLMProvider:
    """LLM_PROVIDER 환경변수에 맞는 Provider를 돌려준다."""
    s = get_settings()
    if s.llm_provider == "ollama":
        from app.llm.ollama import OllamaProvider

        return OllamaProvider(s.ollama_base_url, s.ollama_model)
    from app.llm.mock import MockProvider

    return MockProvider()
