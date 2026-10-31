from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.crm import notify_crm
from app.db import connect, insert_call
from app.logging_setup import configure_logging
from app.models import CallCompleted, HealthResponse
from app.retry import schedule_retry

RETRY_DISPOSITIONS = frozenset({"NO_ANSWER", "BUSY"})
configure_logging()

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
def call_completed(body: CallCompleted) -> dict:
    db = app.state.db
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        insert_call(db, body.account_id, body.disposition, body.attempt, created_at)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="persist_failed") from exc

    next_call = None
    if body.disposition in RETRY_DISPOSITIONS:
        next_call = schedule_retry(body.account_id, body.attempt)
        notify_crm(app.state.crm_url, body.account_id, next_call)

    return {
        "status": "ok",
        "next_call": next_call.isoformat() if next_call else None,
    }
