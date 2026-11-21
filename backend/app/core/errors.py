"""에러 코드 카탈로그 (docs/spec/error-handling.md). service는 AppError만 던진다."""

from enum import StrEnum


class ErrorCode(StrEnum):
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVITE_CODE_INVALID = "INVITE_CODE_INVALID"
    CLASS_NOT_STARTED = "CLASS_NOT_STARTED"
    CLASS_FULL = "CLASS_FULL"
    CLASS_EXPIRED = "CLASS_EXPIRED"
    ALREADY_ENROLLED = "ALREADY_ENROLLED"
    ALREADY_SUBMITTED = "ALREADY_SUBMITTED"
    CLASSIFIER_UNAVAILABLE = "CLASSIFIER_UNAVAILABLE"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    RUNNER_UNAVAILABLE = "RUNNER_UNAVAILABLE"

    @property
    def status(self) -> int:
        return _CATALOG[self][0]

    @property
    def default_message(self) -> str:
        return _CATALOG[self][1]


_AI_BUSY = "AI 도움을 잠시 쓸 수 없습니다. 잠시 후 다시 시도해 주세요."

_CATALOG: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.VALIDATION_FAILED: (400, "입력 값이 올바르지 않습니다."),
    ErrorCode.UNAUTHORIZED: (401, "로그인이 필요합니다."),
    ErrorCode.FORBIDDEN: (403, "접근 권한이 없습니다."),
    ErrorCode.NOT_FOUND: (404, "대상을 찾을 수 없습니다."),
    ErrorCode.CONFLICT: (409, "요청이 현재 상태와 충돌합니다."),
    ErrorCode.INTERNAL_ERROR: (500, "일시적인 오류가 발생했습니다."),
    ErrorCode.EMAIL_TAKEN: (409, "이미 가입된 이메일입니다."),
    ErrorCode.INVALID_CREDENTIALS: (401, "이메일 또는 비밀번호가 올바르지 않습니다."),
    ErrorCode.INVITE_CODE_INVALID: (404, "초대 코드를 찾을 수 없습니다."),
    ErrorCode.CLASS_NOT_STARTED: (409, "아직 시작하지 않은 클래스입니다."),
    ErrorCode.CLASS_FULL: (409, "클래스 정원이 가득 찼습니다."),
    ErrorCode.CLASS_EXPIRED: (409, "이용 기간이 끝난 클래스입니다."),
    ErrorCode.ALREADY_ENROLLED: (409, "이미 참여한 클래스입니다."),
    ErrorCode.ALREADY_SUBMITTED: (409, "이미 제출한 과제입니다."),
    ErrorCode.CLASSIFIER_UNAVAILABLE: (503, _AI_BUSY),
    ErrorCode.LLM_UNAVAILABLE: (503, _AI_BUSY),
    ErrorCode.RUNNER_UNAVAILABLE: (503, "코드 실행 환경을 잠시 쓸 수 없습니다. 잠시 후 다시 시도해 주세요."),
}


class AppError(Exception):
    """service가 던지는 예외. 예: AppError(ErrorCode.CLASS_FULL)"""

    def __init__(self, code: ErrorCode, message: str | None = None) -> None:
        super().__init__(code.value)
        self.code = code
        self.message = message or code.default_message
