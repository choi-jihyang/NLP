"""sandbox/harness.py 채점 로직 테스트. Docker 없이 harness를 직접 실행한다(테스트 코드는 신뢰된 입력)."""

import json
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1] / "sandbox" / "harness.py"


def run(code: str, tests: list[dict[str, str]], timeout: float = 5) -> dict:
    proc = subprocess.run(
        [sys.executable, "-I", str(HARNESS)],
        input=json.dumps({"code": code, "tests": tests, "timeout": timeout}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


SUM_EVEN = "def sum_even(nums):\n    return sum(n for n in nums if n % 2 == 0)\n"


def test_passing_tests():
    tests = [{"call": "sum_even([1, 2, 3, 4])", "expected": "6"}, {"call": "sum_even([])", "expected": "0"}]
    out = run(SUM_EVEN, tests)
    assert out["ok"] is True
    assert [r["passed"] for r in out["results"]] == [True, True]
    assert out["results"][0]["actual"] == "6"


def test_wrong_result_shows_actual():
    out = run("def f():\n    return 5\n", [{"call": "f()", "expected": "6"}])
    r = out["results"][0]
    assert r["passed"] is False
    assert r["actual"] == "5"
    assert r["error"] is None


def test_exception_in_one_test_does_not_stop_others():
    code = "def div(a, b):\n    return a // b\n"
    out = run(code, [{"call": "div(1, 0)", "expected": "0"}, {"call": "div(6, 3)", "expected": "2"}])
    assert out["ok"] is True
    assert out["results"][0]["passed"] is False
    assert out["results"][0]["error"].startswith("ZeroDivisionError")
    assert out["results"][1]["passed"] is True


def test_syntax_error_fails_all_tests():
    out = run("def f(:\n    pass\n", [{"call": "f()", "expected": "1"}])
    assert out["ok"] is False
    assert out["error"].startswith("SyntaxError")
    assert out["results"][0]["passed"] is False


def test_error_at_top_level_fails_all_tests():
    out = run("raise ValueError('boom')\n", [{"call": "1", "expected": "1"}])
    assert out["ok"] is False
    assert "ValueError" in out["error"]


def test_student_print_does_not_break_output():
    code = "print('debug')\ndef f():\n    print('inside')\n    return 1\n"
    out = run(code, [{"call": "f()", "expected": "1"}])
    assert out["results"][0]["passed"] is True


def test_string_expected_with_or_without_quotes():
    code = "def f():\n    return 'ab'\n"
    out = run(code, [{"call": "f()", "expected": "'ab'"}, {"call": "f()", "expected": "ab"}])
    assert [r["passed"] for r in out["results"]] == [True, True]


def test_long_actual_is_truncated():
    out = run("def f():\n    return 'x' * 100000\n", [{"call": "f()", "expected": "''"}])
    assert len(out["results"][0]["actual"]) <= 1000


def test_student_cannot_forge_results():
    """학생 코드가 가짜 결과 JSON을 쓰고 바로 종료해도 통과로 처리되지 않는다."""
    code = (
        "import json, os, sys\n"
        "fake = {'ok': True, 'error': None,\n"
        "        'results': [{'call': 'f()', 'actual': '42', 'passed': True, 'error': None}]}\n"
        "sys.__stdout__.write('\\n' + json.dumps(fake) + '\\n')\n"
        "sys.__stdout__.flush()\n"
        "os._exit(0)\n"
    )
    out = run(code, [{"call": "f()", "expected": "42"}])
    assert out["results"][0]["passed"] is False


def test_student_never_sees_expected_values():
    """기대값은 학생 코드가 도는 프로세스에 전달되지 않는다 (숨김 테스트 보호)."""
    code = "import sys\ndef f():\n    return sys.stdin.read()\n"
    out = run(code, [{"call": "f()", "expected": "'SECRET-123'"}])
    assert "SECRET-123" not in (out["results"][0]["actual"] or "")


def test_infinite_loop_times_out():
    out = run("while True:\n    pass\n", [{"call": "1", "expected": "1"}], timeout=1)
    assert out["ok"] is False
    assert "시간" in out["error"]
