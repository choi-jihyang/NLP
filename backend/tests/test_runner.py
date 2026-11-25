import asyncio
import shutil
import subprocess

import pytest

from app.core.config import get_settings
from app.core.enums import Language
from app.runner.base import IOCase, RunnerUnavailableError
from app.runner.docker import DockerRunner
from app.runner.mock import MockRunner

TO_BINARY_C = (
    "#include <stdio.h>\n"
    "int main(void){ int n; scanf(\"%d\", &n); char b[40]; int i = 0;\n"
    "  if (n == 0) { puts(\"0\"); return 0; }\n"
    "  while (n > 0) { b[i++] = '0' + n % 2; n /= 2; }\n"
    "  while (i > 0) putchar(b[--i]); putchar('\\n'); return 0; }\n"
)
TESTS = [IOCase(input="10\n", expected_output="1010"), IOCase(input="0\n", expected_output="0")]
IMAGE = get_settings().runner_image


def test_mock_runner_passes_every_test_and_records_calls():
    runner = MockRunner()
    out = asyncio.run(runner.run(Language.C, TO_BINARY_C, TESTS))
    assert out.ok
    assert [r.passed for r in out.results] == [True, True]
    assert [r.input for r in out.results] == [t.input for t in TESTS]
    assert runner.calls == [(Language.C, TO_BINARY_C, TESTS)]


def test_docker_command_applies_isolation_limits():
    cmd = DockerRunner(image="thinkguard-runner", memory_mb=128, timeout_sec=5).command("tg-run-1")
    joined = " ".join(cmd)
    for flag in ["--rm", "-i", "--pull never", "--network none", "--memory 128m", "--pids-limit",
                 "--read-only", "--cap-drop ALL", "no-new-privileges"]:
        assert flag in joined
    assert "exec" in joined.split("--tmpfs ")[1].split()[0]  # 컴파일 결과 실행 가능
    assert cmd[-1] == "thinkguard-runner"


def test_wall_timeout_grows_with_tests():
    r = DockerRunner(image="x", timeout_sec=2)
    assert r.wall_timeout(10) > r.wall_timeout(1) >= 2


def test_docker_missing_raises_unavailable(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(RunnerUnavailableError):
        asyncio.run(DockerRunner(image="thinkguard-runner").run(Language.C, TO_BINARY_C, TESTS))


def test_unsupported_language_fails_without_docker(monkeypatch):
    monkeypatch.setenv("PATH", "")  # docker를 부르면 RunnerUnavailableError가 나야 하는데 부르지 않는다
    out = asyncio.run(DockerRunner(image="x").run(Language.JAVA, "class A {}", TESTS))
    assert not out.ok and "JAVA" in out.error


def _docker_ok() -> bool:
    return bool(shutil.which("docker")) and subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def _image_ready() -> bool:
    if not _docker_ok():
        return False
    return subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode == 0


docker_only = pytest.mark.skipif(not _image_ready(), reason=f"Docker 또는 {IMAGE} 이미지 없음")


@pytest.mark.skipif(not _docker_ok(), reason="Docker 없음")
def test_missing_image_raises_unavailable_instead_of_pulling():
    runner = DockerRunner(image="thinkguard-runner-does-not-exist")
    with pytest.raises(RunnerUnavailableError):
        asyncio.run(runner.run(Language.C, TO_BINARY_C, TESTS))


@docker_only
def test_real_container_runs_c_tests():
    out = asyncio.run(DockerRunner(image=IMAGE).run(Language.C, TO_BINARY_C, TESTS))
    assert out.ok, out.error
    assert [r.passed for r in out.results] == [True, True]


@docker_only
def test_real_container_has_no_network():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 80), timeout=2)\n"
        "    print('connected')\n"
        "except OSError:\n"
        "    print('blocked')\n"
    )
    out = asyncio.run(DockerRunner(image=IMAGE).run(Language.PYTHON, code, [IOCase(expected_output="blocked")]))
    assert out.results[0].passed, out


@docker_only
def test_real_container_cannot_write_outside_tmp():
    code = (
        "try:\n"
        "    open('/opt/runner/x.txt', 'w').write('x')\n"
        "    print('written')\n"
        "except OSError:\n"
        "    print('denied')\n"
    )
    out = asyncio.run(DockerRunner(image=IMAGE).run(Language.PYTHON, code, [IOCase(expected_output="denied")]))
    assert out.results[0].passed, out


@docker_only
def test_real_container_infinite_loop_times_out():
    runner = DockerRunner(image=IMAGE, timeout_sec=2)
    code = "int main(void){ while (1) {} }"
    out = asyncio.run(runner.run(Language.C, code, [IOCase(expected_output="1")]))
    assert not out.results[0].passed
    assert "시간 초과" in out.results[0].error


@docker_only
def test_real_container_hides_expected_from_student():
    """컨테이너 안(일반 사용자)에서 부모 메모리 읽기 우회가 막히는지."""
    from tests.test_harness import STEAL_FROM_PARENT_PY

    out = asyncio.run(DockerRunner(image=IMAGE).run(
        Language.PYTHON, STEAL_FROM_PARENT_PY, [IOCase(expected_output="SECRET-777")]
    ))
    assert not out.results[0].passed
    assert "SECRET-777" not in (out.results[0].actual_output or "")
