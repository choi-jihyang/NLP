"""코드 실행 인터페이스. 학생이 쓴 코드를 격리된 환경에서 테스트한다.

테스트 모양은 모든 언어 {input, expected_output}(표준 입력 → 표준 출력, schema D23).
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.core.enums import Language


class IOCase(BaseModel):
    input: str = ""
    """표준 입력"""
    expected_output: str
    """기대 표준 출력. 각 줄 끝 공백 · 마지막 줄바꿈은 무시하고 비교한다"""


class RunCaseResult(BaseModel):
    input: str
    actual_output: str | None
    """실제 표준 출력(최대 1000자). 시간 초과면 None"""
    passed: bool
    error: str | None
    """이 테스트에서 난 문제. 예: 실행 시간 초과 (5초), Segmentation fault"""


class RunResult(BaseModel):
    ok: bool
    """False면 컴파일 오류 등으로 테스트를 돌리지 못함. 이때 results는 모두 실패"""
    error: str | None
    results: list[RunCaseResult]


class RunnerUnavailableError(Exception):
    """실행 환경(Docker)을 쓸 수 없음. API는 503(RUNNER_UNAVAILABLE)으로 응답한다."""


SUPPORTED_LANGUAGES = (Language.C, Language.PYTHON)


class CodeRunner(ABC):
    @abstractmethod
    async def run(self, language: Language, code: str, tests: list[IOCase]) -> RunResult:
        """학생 코드와 테스트 목록을 받아 테스트별 결과를 돌려준다. 숨김 테스트 구분은 호출하는 쪽이 한다."""


def failed(tests: list[IOCase], error: str) -> RunResult:
    results = [RunCaseResult(input=t.input, actual_output=None, passed=False, error=error) for t in tests]
    return RunResult(ok=False, error=error, results=results)
