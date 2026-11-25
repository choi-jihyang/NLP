"""Docker 컨테이너에서 학생 코드를 실행한다 (CODE_RUNNER=docker).

실행마다 새 컨테이너를 띄우고 끝나면 지운다(--rm). 컨테이너 안의 sandbox/harness.py가 컴파일·실행·비교를 한다.
"""

import asyncio
import json
import uuid

from app.core.enums import Language
from app.runner.base import SUPPORTED_LANGUAGES, CodeRunner, IOCase, RunnerUnavailableError, RunResult, failed

# 컨테이너가 뜨는 데 걸리는 시간 여유 + 컴파일 시간 제한(harness COMPILE_TIMEOUT)
_STARTUP_SLACK_SEC = 10
_COMPILE_SEC = 15
_OOM_EXIT_CODE = 137
_UNAVAILABLE_HINTS = ("Cannot connect", "docker daemon", "No such image", "pull access denied")


class DockerRunner(CodeRunner):
    def __init__(self, image: str, timeout_sec: float = 5.0, memory_mb: int = 128):
        self._image = image
        self._timeout = timeout_sec
        self._memory_mb = memory_mb

    def command(self, name: str) -> list[str]:
        """격리 옵션을 붙인 docker run 명령."""
        return [
            "docker", "run", "--rm", "-i",
            "--pull", "never",                   # 이미지가 없으면 받지 않고 바로 실패 → RUNNER_UNAVAILABLE
            "--name", name,
            "--network", "none",                 # 인터넷 차단
            "--memory", f"{self._memory_mb}m",   # 메모리 제한
            "--memory-swap", f"{self._memory_mb}m",
            "--cpus", "0.5",
            "--pids-limit", "64",                # 프로세스 폭탄 방지
            "--read-only",                       # 파일 시스템 쓰기 차단
            # 컴파일 결과를 실행해야 해서 exec 허용(기본 tmpfs는 noexec). 크기 제한으로 출력 폭탄도 막는다
            "--tmpfs", "/tmp:rw,exec,nosuid,nodev,size=32m,mode=1777",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            self._image,
        ]  # fmt: skip

    def wall_timeout(self, n_tests: int) -> float:
        """컨테이너 전체 시간 제한: 컴파일 + 테스트마다 시간 제한 + 여유."""
        return _COMPILE_SEC + self._timeout * max(n_tests, 1) + _STARTUP_SLACK_SEC

    async def run(self, language: Language, code: str, tests: list[IOCase]) -> RunResult:
        if language not in SUPPORTED_LANGUAGES:
            return failed(tests, f"아직 실행할 수 없는 언어예요: {language.value}")
        name = f"tg-run-{uuid.uuid4().hex[:12]}"
        payload = json.dumps({
            "language": language.value, "code": code,
            "tests": [t.model_dump() for t in tests], "timeout": self._timeout,
        })  # fmt: skip
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
                proc.communicate(payload.encode()), timeout=self.wall_timeout(len(tests))
            )
        except TimeoutError:
            await _kill(name)
            proc.kill()
            return failed(tests, f"실행 시간 초과 ({self._timeout:g}초)")

        if proc.returncode == _OOM_EXIT_CODE:
            return failed(tests, f"메모리 제한 초과 ({self._memory_mb}MB)")
        lines = stdout.decode(errors="replace").strip().splitlines()
        if proc.returncode != 0 or not lines:
            detail = stderr.decode(errors="replace").strip()
            if any(h in detail for h in _UNAVAILABLE_HINTS):
                raise RunnerUnavailableError(detail[:200])
            return failed(tests, "코드 실행 환경 오류")
        return RunResult.model_validate(json.loads(lines[-1]))


async def _kill(name: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "docker", "kill", name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
