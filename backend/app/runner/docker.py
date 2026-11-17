"""Docker 컨테이너에서 학생 코드를 실행한다 (CODE_RUNNER=docker).

실행마다 새 컨테이너를 띄우고 끝나면 지운다(--rm). 컨테이너 안의 sandbox/harness.py가 실제 실행·비교를 한다.
"""

import asyncio
import json
import uuid

from app.runner.base import CodeRunner, RunnerUnavailableError, RunResult, TestCase, TestResult

# 컨테이너가 뜨는 데 걸리는 시간 여유. 학생 코드 시간 제한은 harness 안에서 timeout_sec로 건다
_STARTUP_SLACK_SEC = 10
_OOM_EXIT_CODE = 137


class DockerRunner(CodeRunner):
    def __init__(self, image: str, timeout_sec: float = 5.0, memory_mb: int = 128):
        self._image = image
        self._timeout = timeout_sec
        self._memory_mb = memory_mb

    def command(self, name: str) -> list[str]:
        """격리 옵션을 붙인 docker run 명령."""
        return [
            "docker", "run", "--rm", "-i",
            "--name", name,
            "--network", "none",                 # 인터넷 차단
            "--memory", f"{self._memory_mb}m",   # 메모리 제한
            "--memory-swap", f"{self._memory_mb}m",
            "--cpus", "0.5",
            "--pids-limit", "64",                # 프로세스 폭탄 방지
            "--read-only",                       # 파일 시스템 쓰기 차단
            "--tmpfs", "/tmp:size=16m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            self._image,
        ]  # fmt: skip

    async def run(self, code: str, tests: list[TestCase]) -> RunResult:
        name = f"tg-run-{uuid.uuid4().hex[:12]}"
        payload = json.dumps({"code": code, "tests": [t.model_dump() for t in tests], "timeout": self._timeout})
        try:
            proc = await asyncio.create_subprocess_exec(
                *self.command(name),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise RunnerUnavailableError("docker 명령을 찾을 수 없습니다") from exc

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(payload.encode()), timeout=self._timeout + _STARTUP_SLACK_SEC
            )
        except TimeoutError:
            await _kill(name)
            proc.kill()
            return _failed(tests, f"실행 시간 초과 ({self._timeout:g}초)")

        if proc.returncode == _OOM_EXIT_CODE:
            return _failed(tests, f"메모리 제한 초과 ({self._memory_mb}MB)")
        lines = stdout.decode(errors="replace").strip().splitlines()
        if proc.returncode != 0 or not lines:
            detail = stderr.decode(errors="replace").strip()
            if "Cannot connect" in detail or "docker daemon" in detail or "No such image" in detail:
                raise RunnerUnavailableError(detail[:200])
            return _failed(tests, "코드 실행 환경 오류")
        return RunResult.model_validate(json.loads(lines[-1]))


def _failed(tests: list[TestCase], error: str) -> RunResult:
    results = [TestResult(call=t.call, actual=None, passed=False, error=error) for t in tests]
    return RunResult(ok=False, error=error, results=results)


async def _kill(name: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "docker", "kill", name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
