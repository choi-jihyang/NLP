from datetime import date, datetime, timedelta

from app.core.clock import KST, add_years, now_kst, start_of_day_kst


def test_now_kst_has_plus_nine_offset():
    now = now_kst()
    assert now.utcoffset() == timedelta(hours=9)


def test_start_of_day_kst():
    assert start_of_day_kst(date(2027, 3, 2)) == datetime(2027, 3, 2, 0, 0, tzinfo=KST)
    assert start_of_day_kst(date(2027, 3, 2)).isoformat() == "2027-03-02T00:00:00+09:00"


def test_add_years_normal_day():
    start = datetime(2026, 11, 21, 0, 0, tzinfo=KST)
    assert add_years(start, 1) == datetime(2027, 11, 21, 0, 0, tzinfo=KST)


def test_add_years_leap_day_falls_back_to_feb_28():
    start = datetime(2028, 2, 29, 0, 0, tzinfo=KST)
    assert add_years(start, 1) == datetime(2029, 2, 28, 0, 0, tzinfo=KST)
