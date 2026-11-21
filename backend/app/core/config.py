from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 읽는 설정. 항목 설명은 .env.example 참고."""

    # hide_input_in_errors: 잘못된 비밀키 값이 오류 메시지·로그에 찍히지 않게
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    database_url: str = "sqlite:///./thinkguard.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    llm_provider: Literal["mock", "ollama"] = "mock"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    classifier: Literal["stub", "module", "http"] = "stub"
    classifier_module: str = "thinkguard_nlp.classifier:classify"
    classifier_url: str = "http://localhost:8001/classify"
    classifier_min_confidence: float = 0.5

    code_runner: Literal["mock", "docker"] = "mock"
    runner_image: str = "thinkguard-runner"
    runner_timeout_sec: float = 5.0
    runner_memory_mb: int = 128

    jwt_secret: str = Field(default="", validate_default=True)
    teacher_token_hours: int = Field(default=12, ge=1)

    @field_validator("jwt_secret")
    @classmethod
    def _secret_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET은 32자 이상이어야 합니다. backend/.env에 무작위 값을 넣으세요.")
        return value


def load_settings(**overrides: Any) -> Settings:
    """설정이 잘못되면 긴 traceback 대신 한 줄 안내로 멈춘다(값은 출력하지 않음)."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        reasons = " / ".join(str(err["msg"]).removeprefix("Value error, ") for err in exc.errors())
        raise SystemExit(f"설정 오류: {reasons}") from None


@lru_cache
def get_settings() -> Settings:
    return load_settings()
