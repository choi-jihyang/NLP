"""sandbox/harness.py 채점 로직 테스트. Docker 없이 harness를 직접 실행한다(테스트 코드는 신뢰된 입력).

C 테스트는 이 PC에 gcc가 있어야 돈다(없으면 건너뜀).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1] / "sandbox" / "harness.py"
needs_gcc = pytest.mark.skipif(not shutil.which("gcc"), reason="gcc 없음")
needs_linux_non_root = pytest.mark.skipif(
    not sys.platform.startswith("linux") or os.geteuid() == 0,
    reason="리눅스 일반 사용자에서만 의미 있음(root는 /proc 보호를 무시)",
)


def run(code: str, tests: list[dict[str, str]], language: str = "C", timeout: float = 5) -> dict:
    proc = subprocess.run(
        [sys.executable, "-I", str(HARNESS)],
        input=json.dumps({"language": language, "code": code, "tests": tests, "timeout": timeout}),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def io(inp: str, out: str) -> dict[str, str]:
    return {"input": inp, "expected_output": out}


TO_BINARY_C = r"""
#include <stdio.h>
int main(void) {
    int n; if (scanf("%d", &n) != 1) return 0;
    char buf[40]; int i = 0;
    if (n == 0) { puts("0"); return 0; }
    while (n > 0) { buf[i++] = '0' + n % 2; n /= 2; }
    while (i > 0) putchar(buf[--i]);
    putchar('\n');
    return 0;
}
"""


# ---- C ----------------------------------------------------------------------


@needs_gcc
def test_c_passing_tests_and_actual_output():
    out = run(TO_BINARY_C, [io("10\n", "1010"), io("0\n", "0\n")])
    assert out["ok"] is True
    assert [r["passed"] for r in out["results"]] == [True, True]
    assert out["results"][0]["actual_output"] == "1010\n"


@needs_gcc
def test_c_wrong_output_shows_actual():
    out = run(TO_BINARY_C, [io("5\n", "100")])
    r = out["results"][0]
    assert r["passed"] is False and r["actual_output"] == "101\n" and r["error"] is None


@needs_gcc
def test_c_compile_error_fails_all_with_message():
    out = run("int main(void) { return 0 }", [io("", ""), io("1", "1")])
    assert out["ok"] is False
    assert out["error"].startswith("컴파일 오류")
    assert "main.c" in out["error"] and "/tmp" not in out["error"]
    assert [r["passed"] for r in out["results"]] == [False, False]


@needs_gcc
def test_c_trailing_spaces_and_final_newline_are_ignored():
    code = '#include <stdio.h>\nint main(void){ printf("1 2 \\n3\\n\\n"); return 0; }'
    assert run(code, [io("", "1 2\n3")])["results"][0]["passed"] is True
    # 줄 안의 공백 · 빈 줄 개수(마지막 제외)는 무시하지 않는다
    assert run(code, [io("", "12\n3")])["results"][0]["passed"] is False


@needs_gcc
def test_c_infinite_loop_times_out_per_test():
    code = "#include <stdio.h>\nint main(void){ int n; scanf(\"%d\", &n); while (n) {} puts(\"0\"); return 0; }"
    out = run(code, [io("1", "0"), io("0", "0")], timeout=1)
    assert out["ok"] is True
    assert out["results"][0]["passed"] is False and "시간 초과" in out["results"][0]["error"]
    assert out["results"][1]["passed"] is True


@needs_gcc
def test_c_segfault_is_reported():
    code = "int main(void){ int *p = 0; *p = 1; return 0; }"
    r = run(code, [io("", "")])["results"][0]
    assert r["passed"] is False and "Segmentation" in r["error"]


@needs_gcc
def test_c_nonzero_exit_is_reported_but_output_still_compared():
    code = '#include <stdio.h>\nint main(void){ puts("7"); return 3; }'
    r = run(code, [io("", "7")])["results"][0]
    assert r["passed"] is True and "종료 코드 3" in r["error"]


@needs_gcc
def test_c_output_flood_is_truncated():
    code = '#include <stdio.h>\nint main(void){ for (int i = 0; i < 2000000; i++) putchar(\'x\'); return 0; }'
    r = run(code, [io("", "x")])["results"][0]
    assert r["passed"] is False and len(r["actual_output"]) <= 1000


@needs_gcc
def test_c_forged_result_line_does_not_pass():
    """학생 프로그램이 가짜 결과 JSON을 출력해도 그것은 그 테스트의 '실제 출력'일 뿐이다."""
    fake = json.dumps({"ok": True, "error": None, "results": [{"input": "", "actual_output": "42",
                                                               "passed": True, "error": None}]})
    escaped = fake.replace('"', '\\"')
    code = '#include <stdio.h>\nint main(void){ puts("' + escaped + '"); return 0; }'
    out = run(code, [io("", "42")])
    assert out["results"][0]["passed"] is False


# ---- 숨김 기대값 보호 ---------------------------------------------------------

STEAL_FROM_PARENT_PY = r'''
import os, re, sys
try:
    ppid = os.getppid()
    found = []
    with open(f"/proc/{ppid}/maps") as m, open(f"/proc/{ppid}/mem", "rb", 0) as mem:
        for line in m:
            parts = line.split()
            if "rw" not in parts[1]:
                continue
            a, b = (int(x, 16) for x in parts[0].split("-"))
            try:
                mem.seek(a); chunk = mem.read(b - a)
            except OSError:
                continue
            found += re.findall(rb"SECRET-[0-9]+", chunk)
    print(found[0].decode() if found else "not found")
except OSError as e:
    print("blocked", type(e).__name__)
'''

WRITE_TO_PARENT_STDOUT_PY = r'''
import os
try:
    os.open(f"/proc/{os.getppid()}/fd/1", os.O_WRONLY)
    print("opened")
except OSError:
    print("blocked")
'''


def test_student_stdin_has_only_its_input():
    out = run("import sys\nprint(sys.stdin.read())", [io("hello", "'SECRET-123'")], language="PYTHON")
    assert "SECRET" not in (out["results"][0]["actual_output"] or "")


@needs_linux_non_root
def test_student_cannot_read_expected_from_parent_memory():
    """같은 사용자인 자식이 /proc/<부모>/mem에서 숨김 기대값을 꺼내 출력하는 우회(코드 리뷰 11/18)."""
    out = run(STEAL_FROM_PARENT_PY, [io("", "SECRET-777")], language="PYTHON")
    r = out["results"][0]
    assert r["passed"] is False
    assert "SECRET-777" not in (r["actual_output"] or "")


@needs_linux_non_root
def test_student_cannot_open_parent_stdout():
    out = run(WRITE_TO_PARENT_STDOUT_PY, [io("", "blocked")], language="PYTHON")
    assert out["results"][0]["passed"] is True


# ---- Python · 기타 ------------------------------------------------------------


def test_python_io_program():
    code = "n = int(input())\nprint(bin(n)[2:])\n"
    out = run(code, [io("10\n", "1010"), io("3", "11")], language="PYTHON")
    assert [r["passed"] for r in out["results"]] == [True, True]


def test_python_exception_is_reported_as_nonzero_exit():
    r = run("raise ValueError('boom')", [io("", "")], language="PYTHON")["results"][0]
    assert "종료 코드" in r["error"]


def test_unsupported_language_fails_all():
    out = run("class Main {}", [io("", "")], language="JAVA")
    assert out["ok"] is False and "JAVA" in out["error"]


def test_python_infinite_loop_times_out():
    out = run("while True:\n    pass\n", [io("", "1")], language="PYTHON", timeout=1)
    assert "시간 초과" in out["results"][0]["error"]
