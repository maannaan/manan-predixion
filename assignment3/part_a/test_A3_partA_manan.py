from datetime import datetime, timezone

import pytest

from A3_partA_manan import IST, schedule_retry


def ist(h, m, day=1):
    return datetime(2026, 11, day, h, m, tzinfo=IST)


@pytest.mark.parametrize("now, attempt, expected", [
    (ist(7, 30), 0, ist(8, 0)),          # 08:00 exactly is allowed
    (ist(18, 45), 0, ist(8, 0, day=2)),  # 19:15 -> next day 08:00
    (ist(23, 0), 0, ist(8, 0, day=2)),   # 23:30 -> next day 08:00
    (ist(23, 0), 2, ist(8, 0, day=2)),   # 03:00 next day -> 08:00 that day
    (ist(2, 0), 0, ist(8, 0)),           # 02:30 -> 08:00 same day
    (ist(18, 0), 0, ist(18, 30)),        # inside window, unchanged
    (ist(18, 30), 0, ist(8, 0, day=2)),  # 19:00 exactly is outside
    (ist(10, 0), 1, ist(12, 0)),         # second gap is 120 min
])
def test_schedule_retry(now, attempt, expected):
    assert schedule_retry(attempt, now=now) == expected


def test_no_retry_after_last_attempt():
    assert schedule_retry(3, now=ist(10, 0)) is None


def test_negative_attempt_rejected():
    with pytest.raises(ValueError):
        schedule_retry(-1, now=ist(10, 0))


def test_utc_input_is_converted_to_ist():
    # containers run in UTC: 12:00 UTC = 17:30 IST, +30 min = 18:00 IST
    assert schedule_retry(0, now=datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)) == ist(18, 0)