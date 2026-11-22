"""서버의 모든 시각은 KST(+09:00). 현재 시각은 now_kst()로만 만든다."""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    return datetime.now(KST)


def start_of_day_kst(d: date) -> datetime:
    """그날 00:00 KST. 클래스 시작 날짜 → starts_at."""
    return datetime.combine(d, time.min, tzinfo=KST)


def add_years(dt: datetime, years: int) -> datetime:
    """dt에서 years년 뒤. 2월 29일은 다음 해에 없으므로 2월 28일로."""
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, day=28)
