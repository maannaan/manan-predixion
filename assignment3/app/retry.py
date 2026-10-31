from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
RETRY_GAPS_MIN = [30, 120, 240]  # gap before attempt 1, 2, 3
CALL_START = time(8, 0)
CALL_END = time(19, 0)


def schedule_retry(
    account_id: str,
    attempt: int,
    now: datetime | None = None,
) -> datetime | None:
    """Return next IST call time, or None when retries are exhausted.

    Calling window is 08:00–19:00 IST inclusive of 19:00. Times after 19:00
    roll to 08:00 the next day; times before 08:00 snap to 08:00 the same day.
    """
    if attempt < 0 or attempt >= len(RETRY_GAPS_MIN):
        return None
    if now is None:
        now = datetime.now(IST)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    else:
        now = now.astimezone(IST)

    nxt = (now + timedelta(minutes=RETRY_GAPS_MIN[attempt])).astimezone(IST)
    if nxt.time() > CALL_END:
        nxt = (nxt + timedelta(days=1)).replace(
            hour=CALL_START.hour, minute=0, second=0, microsecond=0
        )
    elif nxt.time() < CALL_START:
        nxt = nxt.replace(hour=CALL_START.hour, minute=0, second=0, microsecond=0)
    return nxt
