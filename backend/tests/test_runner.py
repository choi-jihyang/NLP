import asyncio
import shutil
import subprocess

import pytest

from app.runner.base import RunnerUnavailableError, TestCase
from app.runner.docker import DockerRunner
from app.runner.mock import MockRunner

SUM_EVEN = "def sum_even(nums):\n    return sum(n for n in nums if n % 2 == 0)\n"
TESTS = [TestCase(call="sum_even([1, 2, 3, 4])", expected="6"), TestCase(call="sum_even([])", expected="0")]


def test_mock_runner_passes_every_test_and_records_calls():
    runner = MockRunner()
    out = asyncio.run(runner.run(SUM_EVEN, TESTS))
    assert out.ok
    assert [r.passed for r in out.results] == [True, True]
    assert [r.call for r in out.results] == [t.call for t in TESTS]
    assert runner.calls == [(SUM_EVEN, TESTS)]


def test_docker_command_applies_isolation_limits():
    cmd = DockerRunner(image="thinkguard-runner", memory_mb=128, timeout_sec=5).command("tg-run-1")
    joined = " ".join(cmd)
    for flag in ["--rm", "-i", "--network none", "--memory 128m", "--pids-limit", "--read-only", "--cap-drop ALL"]:
        assert flag in joined
    assert cmd[-1] == "thinkguard-runner"


def test_docker_missing_raises_unavailable(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(RunnerUnavailableError):
        asyncio.run(DockerRunner(image="thinkguard-runner").run(SUM_EVEN, TESTS))


def _image_ready() -> bool:
    if not shutil.which("docker"):
        return False
    probe = subprocess.run(["docker", "image", "inspect", "thinkguard-runner"], capture_output=True)
    return probe.returncode == 0


docker_only = pytest.mark.skipif(not _image_ready(), reason="Docker 또는 thinkguard-runner 이미지 없음")


@docker_only
def test_real_container_runs_tests():
    out = asyncio.run(DockerRunner(image="thinkguard-runner").run(SUM_EVEN, TESTS))
    assert out.ok
    assert [r.passed for r in out.results] == [True, True]


@docker_only
def test_real_container_has_no_network():
    code = (
        "import socket\n"
        "def f():\n"
        "    try:\n"
        "        socket.create_connection(('1.1.1.1', 80), timeout=2)\n"
        "        return 'connected'\n"
        "    except OSError:\n"
        "        return 'blocked'\n"
    )
    out = asyncio.run(DockerRunner(image="thinkguard-runner").run(code, [TestCase(call="f()", expected="blocked")]))
    assert out.results[0].passed


@docker_only
def test_real_container_cannot_write_files():
    code = (
        "def f():\n"
        "    try:\n"
        "        open('/opt/runner/x.txt', 'w').write('x')\n"
        "        return 'written'\n"
        "    except OSError:\n"
        "        return 'denied'\n"
    )
    out = asyncio.run(DockerRunner(image="thinkguard-runner").run(code, [TestCase(call="f()", expected="denied")]))
    assert out.results[0].passed


@docker_only
def test_real_container_infinite_loop_times_out():
    runner = DockerRunner(image="thinkguard-runner", timeout_sec=2)
    out = asyncio.run(runner.run("while True:\n    pass\n", [TestCase(call="1", expected="1")]))
    assert not out.ok
    assert "시간" in out.error
