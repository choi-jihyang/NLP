from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Integer, create_engine, select
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.core.clock import KST
from app.db.types import KstDateTime


class _Base(DeclarativeBase):
    pass


class _Event(_Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime | None] = mapped_column(KstDateTime())


def test_naive_datetime_rejected():
    with pytest.raises(ValueError, match="시간대"):
        KstDateTime().process_bind_param(datetime(2026, 11, 21, 9, 0), sqlite.dialect())


def test_none_passes_through():
    assert KstDateTime().process_bind_param(None, sqlite.dialect()) is None
    assert KstDateTime().process_result_value(None, sqlite.dialect()) is None


def test_roundtrip_converts_utc_to_kst():
    engine = create_engine("sqlite://")
    _Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(_Event(id=1, at=datetime(2026, 11, 21, 0, 0, tzinfo=UTC)))
        s.commit()
    with Session(engine) as s:
        at = s.scalar(select(_Event.at).where(_Event.id == 1))
    assert at == datetime(2026, 11, 21, 9, 0, tzinfo=KST)
    assert at.utcoffset() == timedelta(hours=9)
    assert at.isoformat() == "2026-11-21T09:00:00+09:00"
