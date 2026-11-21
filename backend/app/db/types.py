"""DB 컬럼 타입. 시각 컬럼은 모두 KstDateTime, Enum 컬럼은 enum_column()을 쓴다."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from app.core.clock import KST


class KstDateTime(TypeDecorator[datetime]):
    """시간대가 있는 datetime만 받아 KST로 저장하고, 읽을 때 +09:00을 붙여 돌려준다.

    SQLite는 시간대를 저장하지 못하므로 KST 기준 시각을 시간대 없이 저장하고,
    읽을 때 KST를 다시 붙인다. PostgreSQL에서는 timestamptz로 저장된다.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("시간대 없는 datetime은 저장할 수 없습니다. now_kst()로 만든 값을 쓰세요.")
        kst = value.astimezone(KST)
        return kst.replace(tzinfo=None) if dialect.name == "sqlite" else kst

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=KST)
        return value.astimezone(KST)


def enum_column(enum_cls: type[StrEnum]) -> SAEnum:
    """StrEnum을 대문자 문자열로 저장하는 컬럼 타입(DB 네이티브 enum은 쓰지 않음)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=20,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )
