from datetime import datetime

from app.retry import IST, schedule_retry


def test_schedule_retry_0730_ist_stays_in_window():
    now = datetime(2026, 8, 3, 7, 30, tzinfo=IST)
    nxt = schedule_retry("A1", 0, now=now)
    assert nxt is not None
    assert nxt.tzinfo is not None
    assert nxt.astimezone(IST) == datetime(2026, 8, 3, 8, 0, tzinfo=IST)


def test_schedule_retry_1845_ist_rolls_to_next_morning():
    now = datetime(2026, 8, 3, 18, 45, tzinfo=IST)
    nxt = schedule_retry("A1", 0, now=now)
    assert nxt is not None
    assert nxt.astimezone(IST) == datetime(2026, 8, 4, 8, 0, tzinfo=IST)


def test_schedule_retry_2300_ist_rolls_to_next_morning():
    now = datetime(2026, 8, 3, 23, 0, tzinfo=IST)
    nxt = schedule_retry("A1", 0, now=now)
    assert nxt is not None
    assert nxt.astimezone(IST) == datetime(2026, 8, 4, 8, 0, tzinfo=IST)


def test_retries_exhausted():
    now = datetime(2026, 8, 3, 10, 0, tzinfo=IST)
    assert schedule_retry("A1", 3, now=now) is None
