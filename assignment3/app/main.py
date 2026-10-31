from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.db import connect, insert_call
from app.logging_setup import configure_logging
from app.models import CallCompleted, HealthResponse
from app.retry import RETRYABLE, notify_crm, schedule_retry

configure_logging()
log = logging.getLogger("call_webhook")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = connect(os.getenv("DATABASE_PATH", "/tmp/calls.db"))
    app.state.crm_url = os.getenv("CRM_URL", "")
    yield
    app.state.db.close()


app = FastAPI(title="call-webhook", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/webhook/call-completed")
async def call_completed(body: CallCompleted) -> dict:
    db = app.state.db
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        insert_call(db, body.account_id, body.disposition, body.attempt, created_at)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="persist_failed") from exc

    next_call = None
    if body.disposition in RETRYABLE:
        next_call = schedule_retry(body.attempt)
        if next_call is not None:
            try:
                await notify_crm(app.state.crm_url, body.account_id, next_call)
            except Exception as exc:  # noqa: BLE001 — CRM outage must not drop the webhook
                log.warning("crm_notify_failed: %s", exc)

    return {
        "status": "ok",
        "next_call": next_call.isoformat() if next_call else None,
    }
