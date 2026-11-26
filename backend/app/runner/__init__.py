from functools import lru_cache

from app.core.config import get_settings
from app.runner.base import (
    SUPPORTED_LANGUAGES,
    CodeRunner,
    IOCase,
    RunCaseResult,
    RunnerUnavailableError,
    RunResult,
)

__all__ = [
    "SUPPORTED_LANGUAGES", "CodeRunner", "IOCase", "RunCaseResult", "RunResult", "RunnerUnavailableError",
    "get_code_runner",
]  # fmt: skip


@lru_cache
def get_code_runner() -> CodeRunner:
    """CODE_RUNNER 환경변수에 맞는 실행기를 돌려준다."""
    s = get_settings()
    if s.code_runner == "docker":
        from app.runner.docker import DockerRunner

        return DockerRunner(s.runner_image, s.runner_timeout_sec, s.runner_memory_mb)
    from app.runner.mock import MockRunner

    return MockRunner()
