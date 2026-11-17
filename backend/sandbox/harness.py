"""컨테이너 안에서 학생 코드와 테스트를 실행하는 스크립트.

입력(stdin, JSON):  {"code": str, "tests": [{"call": str, "expected": str}], "timeout": float}
출력(stdout 마지막 줄, JSON):
    {"ok": bool, "error": str | null,
     "results": [{"call": str, "actual": str | null, "passed": bool, "error": str | null}]}

구조 — 학생 코드는 별도 자식 프로세스에서 돈다.
- 자식에게는 code와 call만 보낸다. 기대값(expected)은 부모만 가진다 → 학생 코드가 숨김 테스트 값을 볼 수 없다.
- 비교(통과 여부)는 부모가 한다 → 학생 코드가 가짜 결과를 출력하고 종료해도 통과가 되지 않는다.
- 시간 제한도 부모가 건다.

ok=false: 문법 오류, 최상위 실행 중 예외, 시간 초과, 자식 출력 이상 → 테스트를 돌리지 못함.
expected는 Python 리터럴로 읽어 값으로 비교하고, 리터럴이 아니면 문자열로 비교한다.
표준 라이브러리만 쓴다. 컨테이너 이미지에 그대로 복사된다.
"""

import ast
import contextlib
import io
import json
import os
import signal
import subprocess
import sys

MAX_ACTUAL = 1000  # 화면에 보여 줄 실제 값 길이
MAX_REPR = 10_000  # 비교에 쓰는 실제 값 최대 길이
MAX_ERROR = 300
DEFAULT_TIMEOUT = 5.0


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _error_text(exc: BaseException) -> str:
    if isinstance(exc, SyntaxError):
        return _short(f"SyntaxError: {exc.msg} (line {exc.lineno})", MAX_ERROR)
    return _short(f"{type(exc).__name__}: {exc}", MAX_ERROR)


# ---------- 자식: 학생 코드 실행 ----------


class _Discard(io.TextIOBase):
    """학생 코드의 print 출력을 버린다."""

    def write(self, s: str) -> int:
        return len(s)


def _student_main() -> None:
    payload = json.loads(sys.stdin.read())
    out_fd = os.dup(1)  # 결과를 쓸 통로. 학생 print는 버린다
    namespace: dict[str, object] = {"__name__": "__student__"}
    values: list[dict[str, str | None]] = []
    error = None
    with contextlib.redirect_stdout(_Discard()):
        try:
            exec(compile(payload["code"], "<student>", "exec"), namespace)
        except BaseException as exc:  # noqa: BLE001 — 학생 코드의 어떤 예외도 결과로 돌려준다
            error = _error_text(exc)
        if error is None:
            for call in payload["calls"]:
                try:
                    values.append({"repr": repr(eval(call, namespace))[:MAX_REPR], "error": None})
                except BaseException as exc:  # noqa: BLE001
                    values.append({"repr": None, "error": _error_text(exc)})
    os.write(out_fd, ("\n" + json.dumps({"error": error, "values": values}) + "\n").encode())


# ---------- 부모: 실행·비교 ----------


def _literal(text: str) -> tuple[bool, object]:
    try:
        return True, ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return False, None


def _matches(actual_repr: str, expected: str) -> bool:
    a_ok, actual = _literal(actual_repr)
    e_ok, want = _literal(expected)
    if e_ok:
        return a_ok and actual == want
    # 기대값이 리터럴이 아님: repr 그대로 또는 문자열 값으로 비교 (예: expected "ab" ↔ 반환값 'ab')
    return actual_repr == expected or (a_ok and isinstance(actual, str) and actual == expected)


def _fail_all(tests: list[dict[str, str]], error: str) -> dict:
    results = [{"call": t["call"], "actual": None, "passed": False, "error": error} for t in tests]
    return {"ok": False, "error": error, "results": results}


def run(code: str, tests: list[dict[str, str]], timeout: float = DEFAULT_TIMEOUT) -> dict:
    child_input = json.dumps({"code": code, "calls": [t["call"] for t in tests]})
    try:
        proc = subprocess.run(
            [sys.executable, "-I", os.path.abspath(__file__), "--student"],
            input=child_input,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return _fail_all(tests, f"실행 시간 초과 ({timeout:g}초)")

    if proc.returncode == -signal.SIGKILL:
        return _fail_all(tests, "메모리 제한을 넘어 실행이 중단됐어요")
    lines = proc.stdout.strip().splitlines()
    try:
        child = json.loads(lines[-1])
        values = child["values"]
    except (IndexError, ValueError, KeyError, TypeError):
        return _fail_all(tests, "코드 실행이 비정상적으로 끝났어요 (예: 프로그램 종료 호출)")
    if child.get("error"):
        return _fail_all(tests, child["error"])
    if len(values) != len(tests):
        return _fail_all(tests, "코드 실행이 비정상적으로 끝났어요")

    results = []
    for t, v in zip(tests, values, strict=True):
        actual = v.get("repr")
        results.append(
            {
                "call": t["call"],
                "actual": None if actual is None else _short(actual, MAX_ACTUAL),
                "passed": actual is not None and _matches(actual, t["expected"]),
                "error": v.get("error"),
            }
        )
    return {"ok": True, "error": None, "results": results}


def main() -> None:
    if "--student" in sys.argv:
        _student_main()
        return
    payload = json.loads(sys.stdin.read())
    out = run(payload["code"], payload["tests"], float(payload.get("timeout", DEFAULT_TIMEOUT)))
    sys.stdout.write("\n" + json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
