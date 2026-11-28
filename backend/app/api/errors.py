"""예외 → {code, message, trace_id}. trace_id는 응답 헤더 X-Request-Id와 같다."""

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError, ErrorCode

REQUEST_ID_HEADER = "X-Request-Id"
logger = logging.getLogger("thinkguard")


def _trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    return trace_id if isinstance(trace_id, str) else uuid.uuid4().hex


def _error(request: Request, code: ErrorCode, message: str) -> JSONResponse:
    trace_id = _trace_id(request)
    return JSONResponse(
        status_code=code.status,
        content={"code": code.value, "message": message, "trace_id": trace_id},
        headers={REQUEST_ID_HEADER: trace_id},
    )


async def _app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return _error(request, exc.code, exc.message)


# 위반 위치를 화면에 보여 줄 이름으로: 목록 안이면 'N번째', 자주 쓰는 과제 필드는 한국어
_LIST_LABEL = {"questions": "문항", "tests": "테스트", "choices": "선택지"}
_FIELD_LABEL = {
    "title": "제목", "prompt": "문제", "answer": "정답", "choices": "선택지", "tests": "테스트",
    "expected_output": "기대 출력", "points": "배점", "rubric": "채점 기준",
}


def _where(loc: tuple[int | str, ...]) -> str:
    """('body', 'questions', 1, 'prompt') → '문항 2 문제'. 목록 위치와 마지막 필드만 남긴다."""
    parts: list[str] = []
    for i, key in enumerate(loc):
        nxt = loc[i + 1] if i + 1 < len(loc) else None
        if isinstance(key, str) and key in _LIST_LABEL and isinstance(nxt, int):
            parts.append(f"{_LIST_LABEL[key]} {nxt + 1}")
    last = loc[-1]
    if isinstance(last, str) and last not in ("body", "query", "path"):
        parts.append(_FIELD_LABEL.get(last, last))
    return " ".join(parts)


def _summary(err: dict[str, Any]) -> str:
    """위치 + (직접 쓴 검사 문구가 있으면) 이유. Pydantic 기본 영어 문구는 보여 주지 않는다."""
    where = _where(tuple(err.get("loc") or ()))
    reason = str(err.get("msg", "")).removeprefix("Value error, ") if err.get("type") == "value_error" else ""
    return f"{where} — {reason}" if where and reason else where or reason


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = [s for s in dict.fromkeys(_summary(err) for err in exc.errors()) if s]
    if not fields:
        return _error(request, ErrorCode.VALIDATION_FAILED, ErrorCode.VALIDATION_FAILED.default_message)
    message = "입력 값이 올바르지 않습니다: " + ", ".join(fields)
    return _error(request, ErrorCode.VALIDATION_FAILED, message)


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    trace_id = _trace_id(request)
    logger.error("처리되지 않은 예외 trace_id=%s", trace_id, exc_info=exc)  # 원문은 서버 로그에만
    return _error(request, ErrorCode.INTERNAL_ERROR, ErrorCode.INTERNAL_ERROR.default_message)


def install_error_handling(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled_error)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        trace_id = uuid.uuid4().hex
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        except Exception as exc:  # CORS 안쪽에서 500을 만들어야 브라우저가 에러 본문을 읽을 수 있다
            response = await _unhandled_error(request, exc)
        response.headers[REQUEST_ID_HEADER] = trace_id
        return response
