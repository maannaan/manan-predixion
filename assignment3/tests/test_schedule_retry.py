from datetime import datetime, timezone

import pytest

from app.retry import IST, schedule_retry


def ist(hour: int, minute: int, day: int = 3) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=IST)


def test_schedule_retry_0730_ist_stays_in_window():
    nxt = schedule_retry(0, now=ist(7, 30))
    assert nxt == ist(8, 0)


def test_schedule_retry_1845_ist_rolls_to_next_morning():
    nxt = schedule_retry(0, now=ist(18, 45))
    assert nxt == ist(8, 0, day=4)


def test_schedule_retry_2300_ist_rolls_to_next_morning():
    nxt = schedule_retry(0, now=ist(23, 0))
    assert nxt == ist(8, 0, day=4)


def test_nineteen_hundred_is_outside_window():
    nxt = schedule_retry(0, now=ist(18, 30))
    assert nxt == ist(8, 0, day=4)


def test_retries_exhausted():
    assert schedule_retry(3, now=ist(10, 0)) is None


def test_negative_attempt_rejected():
    with pytest.raises(ValueError):
        schedule_retry(-1, now=ist(10, 0))


def test_utc_input_converted_to_ist():
    nxt = schedule_retry(0, now=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc))
    assert nxt == ist(18, 0)
