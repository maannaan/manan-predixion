from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx

log = logging.getLogger("call_webhook")

IST = ZoneInfo("Asia/Kolkata")
RETRY_GAPS_MIN = [30, 120, 240]   # gap before attempt 1, 2, 3
WINDOW_START = time(8, 0)         # calling allowed 08:00-19:00 IST
WINDOW_END = time(19, 0)          # 19:00 itself is outside the window
RETRYABLE = {"NO_ANSWER", "BUSY"}


def schedule_retry(attempt: int, now: datetime | None = None) -> datetime | None:
    """Return the next call time in IST, or None if no retries are left."""
    if attempt < 0:
        raise ValueError(f"attempt must be >= 0, got {attempt}")
    if attempt >= len(RETRY_GAPS_MIN):
        return None

    now = (now or datetime.now(tz=IST)).astimezone(IST)
    next_time = now + timedelta(minutes=RETRY_GAPS_MIN[attempt])

    if next_time.time() < WINDOW_START:
        # e.g. 02:30 -> 08:00 the same day
        next_time = next_time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif next_time.time() >= WINDOW_END:
        # e.g. 19:15 -> 08:00 the next day
        next_time = (next_time + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
    return next_time


async def notify_crm(crm_url: str, account_id: str, next_call: datetime,
                     attempts: int = 5) -> dict:
    """POST the retry to the CRM with a timeout and exponential backoff."""
    payload = {"account_id": account_id, "next_call": next_call.isoformat()}
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        for i in range(attempts):
            try:
                r = await client.post(crm_url, json=payload)
                r.raise_for_status()
                return r.json()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                log.warning("crm call failed", extra={"account_id": account_id,
                                                      "try": i + 1, "error": str(exc)})
                if i == attempts - 1:
                    raise                           
                await asyncio.sleep(min(2 ** i, 30)) 
    raise RuntimeError("unreachable")