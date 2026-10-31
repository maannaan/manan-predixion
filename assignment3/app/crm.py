from __future__ import annotations

import logging
from datetime import datetime

import httpx

log = logging.getLogger(__name__)


def notify_crm(crm_url: str, account_id: str, next_call: datetime | None, timeout_s: float = 5.0) -> bool:
    if not crm_url or next_call is None:
        return False
    payload = {"account_id": account_id, "next_call": next_call.isoformat()}
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.post(crm_url, json=payload, timeout=timeout_s)
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            last_error = exc
            log.warning("crm_notify_failed", extra={"attempt": attempt})
    log.error("crm_notify_gave_up: %s", last_error)
    return False
