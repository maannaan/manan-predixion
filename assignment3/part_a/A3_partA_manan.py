from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx

log = logging.getLogger("call_webhook")

IST = ZoneInfo("Asia/Kolkata")
RETRY_GAPS_MIN = [30, 120, 240]   
WINDOW_START = time(8, 0)         
WINDOW_END = time(19, 0)          
RETRYABLE = {"NO_ANSWER", "BUSY"}


def schedule_retry(attempt: int, now: datetime | None = None) -> datetime | None:
    if attempt < 0:
        raise ValueError(f"attempt must be >= 0, got {attempt}")
    if attempt >= len(RETRY_GAPS_MIN):
        return None

    now = (now or datetime.now(tz=IST)).astimezone(IST)
    next_time = now + timedelta(minutes=RETRY_GAPS_MIN[attempt])

    if next_time.time() < WINDOW_START:
        next_time = next_time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif next_time.time() >= WINDOW_END:
        next_time = (next_time + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
    return next_time


async def notify_crm(crm_url: str, account_id: str, next_call: datetime,
                     attempts: int = 5) -> dict:
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