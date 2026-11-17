"""코드 실행 인터페이스. 학생이 쓴 코드를 격리된 환경에서 테스트한다."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class TestCase(BaseModel):
    __test__ = False  # pytest가 테스트 클래스로 오해하지 않게

    call: str
    """실행할 호출식. 예: sum_even([1, 2, 3, 4])"""
    expected: str
    """기대값. Python 리터럴(예: 6, 'ab', [1, 2])로 쓰면 값으로 비교한다"""


class TestResult(BaseModel):
    __test__ = False

    call: str
    actual: str | None
    """실제 반환값의 repr. 오류가 나면 None"""
    passed: bool
    error: str | None
    """이 호출에서 난 예외. 예: ZeroDivisionError: division by zero"""


class RunResult(BaseModel):
    ok: bool
    """False면 문법 오류·시간 초과 등으로 테스트를 돌리지 못함. 이때 results는 모두 실패"""
    error: str | None
    results: list[TestResult]


class RunnerUnavailableError(Exception):
    """실행 환경(Docker)을 쓸 수 없음. API는 503으로 응답한다."""


class CodeRunner(ABC):
    @abstractmethod
    async def run(self, code: str, tests: list[TestCase]) -> RunResult:
        """학생 코드와 테스트 목록을 받아 테스트별 결과를 돌려준다. 숨김 테스트 구분은 호출하는 쪽이 한다."""
