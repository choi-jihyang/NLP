from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 읽는 설정. 항목 설명은 .env.example 참고."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./thinkguard.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    llm_provider: Literal["mock", "ollama"] = "mock"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    classifier: Literal["stub", "module", "http"] = "stub"
    classifier_module: str = "thinkguard_nlp.classifier:classify"
    classifier_url: str = "http://localhost:8001/classify"
    classifier_min_confidence: float = 0.5

    code_runner: Literal["mock", "docker"] = "mock"
    runner_image: str = "thinkguard-runner"
    runner_timeout_sec: float = 5.0
    runner_memory_mb: int = 128


@lru_cache
def get_settings() -> Settings:
    return Settings()
