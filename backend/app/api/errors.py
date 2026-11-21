"""예외 → {code, message, trace_id}. trace_id는 응답 헤더 X-Request-Id와 같다."""

import logging
import uuid
from collections.abc import Awaitable, Callable

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


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = sorted({str(err["loc"][-1]) for err in exc.errors() if err.get("loc")})
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
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = trace_id
        return response
