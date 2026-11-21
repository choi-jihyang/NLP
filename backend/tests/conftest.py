import os

TEST_JWT_SECRET = "test-only-jwt-secret-0123456789abcdef"  # 테스트 전용 값
os.environ.setdefault("JWT_SECRET", TEST_JWT_SECRET)

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.init_db import init_db  # noqa: E402
from app.db.session import create_db_engine, get_db  # noqa: E402


@pytest.fixture
def db() -> Iterator[Session]:
    """테스트마다 새 메모리 SQLite. 외래 키 검사 켜짐."""
    engine = create_db_engine("sqlite://")
    init_db(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """실제 앱 + 메모리 DB. lifespan을 돌리지 않으므로 thinkguard.db를 건드리지 않는다."""
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()
