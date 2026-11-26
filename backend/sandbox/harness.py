"""컨테이너 안에서 학생 코드를 컴파일·실행하고 표준 출력을 비교하는 스크립트.

입력(stdin, JSON):
    {"language": "C" | "PYTHON", "code": str,
     "tests": [{"input": str, "expected_output": str}], "timeout": float}
출력(stdout 마지막 줄, JSON):
    {"ok": bool, "error": str | null,
     "results": [{"input": str, "actual_output": str | null, "passed": bool, "error": str | null}]}

구조 — 테스트 모양은 모든 언어 {input, expected_output}(표준 입력 → 표준 출력, schema D23).
- 학생 프로그램은 테스트마다 별도 자식 프로세스로 돈다. 자식에게는 그 테스트의 input만 표준 입력으로 준다.
  기대 출력은 부모만 가진다 → 학생 코드가 숨김 테스트 값을 볼 수 없다.
- 부모는 시작하자마자 PR_SET_DUMPABLE=0으로 /proc/<부모>/mem · fd를 같은 사용자에게서도 막는다.
  (같은 uid의 자식이 부모 메모리에서 기대값을 읽거나 부모 출력에 가짜 결과를 쓰는 우회 방지)
- 비교(통과 여부)·시간 제한은 부모가 한다. 출력은 각 줄 끝 공백과 마지막 줄바꿈을 무시한다(D23).
- 자식 출력은 파일(/tmp, 크기 제한 tmpfs)로 받아 앞부분만 읽는다 → 출력 폭탄이 부모 메모리를 채우지 못한다.

ok=false: 컴파일 오류, 지원하지 않는 언어 → 테스트를 돌리지 못함.
표준 라이브러리만 쓴다. 컨테이너 이미지에 그대로 복사된다.
"""

import contextlib
import ctypes
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

MAX_OUTPUT = 64 * 1024  # 비교에 쓰는 실제 출력 최대 바이트
MAX_SHOWN = 1000  # 화면에 보여 줄 실제 출력 길이
MAX_ERROR = 600
DEFAULT_TIMEOUT = 5.0
COMPILE_TIMEOUT = 15.0
SUPPORTED = ("C", "PYTHON")


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def normalize(text: str) -> str:
    """줄 끝 공백 · 마지막 줄바꿈 무시 (D23). \\r\\n도 \\n으로 본다."""
    lines = text.replace("\r\n", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).rstrip("\n")


def _hide_from_children() -> None:
    """같은 사용자의 다른 프로세스가 /proc/<이 프로세스>/mem · fd에 접근하지 못하게 한다(리눅스)."""
    if not sys.platform.startswith("linux"):
        return
    pr_set_dumpable = 4
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(pr_set_dumpable, 0, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_DUMPABLE) 실패")


# ---------- 준비: 컴파일 ----------


def _prepare(language: str, code: str, work: str, timeout: float) -> tuple[list[str] | None, str | None]:
    """실행 명령을 만든다. (명령, None) 또는 (None, 오류 문구)."""
    if language == "PYTHON":
        path = os.path.join(work, "main.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return [sys.executable, "-I", "-S", path], None
    if language == "C":
        src, exe = os.path.join(work, "main.c"), os.path.join(work, "main")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            proc = subprocess.run(
                ["gcc", "-std=c11", "-O1", "-w", "-o", exe, src, "-lm"],
                capture_output=True, text=True, timeout=timeout, cwd=work,
            )  # fmt: skip
        except subprocess.TimeoutExpired:
            return None, "컴파일 시간 초과"
        except FileNotFoundError:
            return None, "C 컴파일러(gcc)를 찾을 수 없어요"
        if proc.returncode != 0:
            msg = proc.stderr.replace(src, "main.c").strip() or "알 수 없는 오류"
            return None, _short("컴파일 오류:\n" + msg, MAX_ERROR)
        return [exe], None
    return None, f"지원하지 않는 언어예요: {language}"


# ---------- 실행: 테스트 하나 ----------


def _kill_group(proc: subprocess.Popen) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)


def _run_one(cmd: list[str], stdin_text: str, work: str, timeout: float) -> tuple[str | None, str | None, bool]:
    """(실제 출력, 오류, 정상 종료 여부)."""
    out_path = os.path.join(work, "stdout.txt")
    with open(out_path, "wb") as out:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.DEVNULL,
            cwd=work, start_new_session=True,  # 자식이 만든 손자까지 한 번에 끝낼 수 있게
        )  # fmt: skip
        try:
            with contextlib.suppress(BrokenPipeError):
                proc.communicate(stdin_text.encode(), timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_group(proc)
            proc.wait()
            return None, f"실행 시간 초과 ({timeout:g}초)", False
        finally:
            _kill_group(proc)
    with open(out_path, "rb") as f:
        actual = f.read(MAX_OUTPUT).decode("utf-8", errors="replace")
    os.remove(out_path)

    rc = proc.returncode
    if rc == -signal.SIGKILL:
        return actual, "메모리 제한을 넘어 실행이 중단됐어요", False
    if rc == -signal.SIGSEGV:
        return actual, "Segmentation fault (잘못된 메모리 접근)", False
    if rc < 0:
        return actual, f"실행이 신호 {signal.Signals(-rc).name}로 중단됐어요", False
    if rc != 0:
        return actual, f"프로그램이 종료 코드 {rc}로 끝났어요", True
    return actual, None, True


# ---------- 전체 ----------


def _fail_all(tests: list[dict[str, str]], error: str) -> dict:
    results = [{"input": t["input"], "actual_output": None, "passed": False, "error": error} for t in tests]
    return {"ok": False, "error": error, "results": results}


def run(language: str, code: str, tests: list[dict[str, str]], timeout: float = DEFAULT_TIMEOUT) -> dict:
    work = tempfile.mkdtemp(prefix="run-")
    try:
        cmd, error = _prepare(language, code, work, COMPILE_TIMEOUT)
        if cmd is None:
            return _fail_all(tests, error or "실행 준비 실패")
        results = []
        for t in tests:
            actual, err, exited = _run_one(cmd, t["input"], work, timeout)
            passed = exited and actual is not None and normalize(actual) == normalize(t["expected_output"])
            shown = None if actual is None else _short(actual, MAX_SHOWN)
            results.append({"input": t["input"], "actual_output": shown, "passed": passed, "error": err})
        return {"ok": True, "error": None, "results": results}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> None:
    _hide_from_children()
    payload = json.loads(sys.stdin.read())
    out = run(
        str(payload.get("language", "C")).upper(), payload["code"], payload["tests"],
        float(payload.get("timeout", DEFAULT_TIMEOUT)),
    )  # fmt: skip
    sys.stdout.write("\n" + json.dumps(out, ensure_ascii=False) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
