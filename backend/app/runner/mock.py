from app.core.enums import Language
from app.runner.base import CodeRunner, IOCase, RunCaseResult, RunResult


class MockRunner(CodeRunner):
    """개발용. 코드를 실행하지 않고 모든 테스트를 통과로 돌려준다 (Docker 없는 PC에서 화면·흐름 개발용)."""

    def __init__(self) -> None:
        self.calls: list[tuple[Language, str, list[IOCase]]] = []

    async def run(self, language: Language, code: str, tests: list[IOCase]) -> RunResult:
        self.calls.append((language, code, list(tests)))
        results = [
            RunCaseResult(input=t.input, actual_output=t.expected_output, passed=True, error=None) for t in tests
        ]
        return RunResult(ok=True, error=None, results=results)
