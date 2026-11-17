from app.runner.base import CodeRunner, RunResult, TestCase, TestResult


class MockRunner(CodeRunner):
    """개발용. 코드를 실행하지 않고 모든 테스트를 통과로 돌려준다 (Docker 없는 PC에서 화면·흐름 개발용)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[TestCase]]] = []

    async def run(self, code: str, tests: list[TestCase]) -> RunResult:
        self.calls.append((code, list(tests)))
        results = [TestResult(call=t.call, actual=t.expected, passed=True, error=None) for t in tests]
        return RunResult(ok=True, error=None, results=results)
