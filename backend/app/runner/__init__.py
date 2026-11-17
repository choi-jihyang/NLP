from functools import lru_cache

from app.core.config import get_settings
from app.runner.base import CodeRunner, RunnerUnavailableError, RunResult, TestCase, TestResult

__all__ = ["CodeRunner", "RunResult", "RunnerUnavailableError", "TestCase", "TestResult", "get_code_runner"]


@lru_cache
def get_code_runner() -> CodeRunner:
    """CODE_RUNNER 환경변수에 맞는 실행기를 돌려준다."""
    s = get_settings()
    if s.code_runner == "docker":
        from app.runner.docker import DockerRunner

        return DockerRunner(s.runner_image, s.runner_timeout_sec, s.runner_memory_mb)
    from app.runner.mock import MockRunner

    return MockRunner()
