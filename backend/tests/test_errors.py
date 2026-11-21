import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.errors import REQUEST_ID_HEADER, install_error_handling
from app.core.errors import AppError, ErrorCode


class _Item(BaseModel):
    name: str


def _app() -> FastAPI:
    """테스트 전용 라우터 (error-handling.md 수용 기준)."""
    app = FastAPI()
    install_error_handling(app)

    @app.get("/full")
    def full() -> None:
        raise AppError(ErrorCode.CLASS_FULL)

    @app.get("/custom")
    def custom() -> None:
        raise AppError(ErrorCode.CONFLICT, "이미 최종 제출했어요.")

    @app.post("/items")
    def items(item: _Item) -> dict[str, str]:
        return {"name": item.name}

    @app.get("/crash")
    def crash() -> None:
        raise RuntimeError("db password=hunter2")

    @app.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_app(), raise_server_exceptions=False)


def test_app_error_uses_catalog(client: TestClient):
    res = client.get("/full")
    assert res.status_code == 409
    assert res.json() == {
        "code": "CLASS_FULL",
        "message": "클래스 정원이 가득 찼습니다.",
        "trace_id": res.headers[REQUEST_ID_HEADER],
    }


def test_app_error_message_override(client: TestClient):
    res = client.get("/custom")
    assert res.status_code == 409
    assert res.json()["message"] == "이미 최종 제출했어요."


def test_validation_error_lists_fields(client: TestClient):
    res = client.post("/items", json={})
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert body["message"] == "입력 값이 올바르지 않습니다: name"
    assert body["trace_id"] == res.headers[REQUEST_ID_HEADER]


def test_unhandled_error_hides_detail(client: TestClient):
    res = client.get("/crash")
    assert res.status_code == 500
    assert res.json() == {
        "code": "INTERNAL_ERROR",
        "message": "일시적인 오류가 발생했습니다.",
        "trace_id": res.headers[REQUEST_ID_HEADER],
    }
    assert "hunter2" not in res.text
    assert "Traceback" not in res.text


def test_success_response_unchanged_but_has_request_id(client: TestClient):
    res = client.get("/ok")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert len(res.headers[REQUEST_ID_HEADER]) == 32


def test_catalog_matches_error_handling_doc():
    assert {c.value: c.status for c in ErrorCode} == {
        "VALIDATION_FAILED": 400, "UNAUTHORIZED": 401, "FORBIDDEN": 403, "NOT_FOUND": 404,
        "CONFLICT": 409, "INTERNAL_ERROR": 500, "EMAIL_TAKEN": 409, "INVALID_CREDENTIALS": 401,
        "INVITE_CODE_INVALID": 404, "CLASS_NOT_STARTED": 409, "CLASS_FULL": 409, "CLASS_EXPIRED": 409,
        "ALREADY_ENROLLED": 409, "ALREADY_SUBMITTED": 409, "CLASSIFIER_UNAVAILABLE": 503,
        "LLM_UNAVAILABLE": 503, "RUNNER_UNAVAILABLE": 503,
    }
