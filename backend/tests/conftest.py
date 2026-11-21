from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import create_db_engine


@pytest.fixture
def db() -> Iterator[Session]:
    """테스트마다 새 메모리 SQLite. 외래 키 검사 켜짐."""
    engine = create_db_engine("sqlite://")
    init_db(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()
