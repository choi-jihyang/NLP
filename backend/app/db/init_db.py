from sqlalchemy import Engine

import app.models  # noqa: F401  모델 등록
from app.db.session import Base


def init_db(engine: Engine) -> None:
    """없는 테이블만 만든다. 컬럼이 바뀌면 thinkguard.db를 지우고 다시 실행한다(마이그레이션 없음)."""
    Base.metadata.create_all(engine)
