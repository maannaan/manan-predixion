from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from langchain_core.tools import tool

from store import IST, Store

CALL_START = time(8, 0)
CALL_END = time(19, 0)
ESCALATE_REASONS = frozenset(
    {"DISPUTE", "ALREADY_PAID", "HARDSHIP", "ABUSE", "WRONG_PERSON", "OTHER"}
)


def _parse_amount(amount: str | float | int | Decimal) -> Decimal | None:
    try:
        value = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value <= 0:
        return None
    return value.quantize(Decimal("0.01"))


def _parse_date(value: str, today: date) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_when(value: str, now: datetime) -> datetime | None:
    raw = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.replace(tzinfo=IST)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        return parsed.astimezone(IST)
    except ValueError:
        return None


def build_tools(store: Store):
    @tool
    def verify_identity(account_id: str, dob: str) -> dict[str, Any]:
        """Confirm the caller is the borrower. dob is YYYY-MM-DD. Required before any account details."""
        acct = store.accounts.get(account_id)
        if acct is None:
            return store.log("verify_identity", {"account_id": account_id, "dob": dob}, {
                "ok": False, "error": "UNKNOWN_ACCOUNT"
            })
        if dob != acct["dob"]:
            store.verified.discard(account_id)
            return store.log("verify_identity", {"account_id": account_id, "dob": dob}, {
                "ok": False, "error": "DOB_MISMATCH"
            })
        store.verified.add(account_id)
        return store.log("verify_identity", {"account_id": account_id, "dob": dob}, {
            "ok": True, "account_id": account_id
        })

    @tool
    def get_account(account_id: str) -> dict[str, Any]:
        """Return outstanding, minimum due, DPD and status. Blocked until verify_identity succeeds."""
        if account_id not in store.verified:
            return store.log("get_account", {"account_id": account_id}, {
                "ok": False, "error": "IDENTITY_NOT_VERIFIED"
            })
        acct = store.accounts.get(account_id)
        if acct is None:
            return store.log("get_account", {"account_id": account_id}, {
                "ok": False, "error": "UNKNOWN_ACCOUNT"
            })
        return store.log("get_account", {"account_id": account_id}, {
            "ok": True,
            "account_id": account_id,
            "outstanding": str(acct["outstanding"]),
            "minimum_due": str(acct["minimum_due"]),
            "dpd": acct["dpd"],
            "status": acct["status"],
        })

    @tool
    def record_promise_to_pay(account_id: str, amount: str, pay_date: str) -> dict[str, Any]:
        """Record a PTP. amount in rupees. pay_date YYYY-MM-DD. Blocked until verified. Date today..today+7. Amount between minimum due and outstanding."""
        args = {"account_id": account_id, "amount": amount, "pay_date": pay_date}
        if account_id not in store.verified:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "IDENTITY_NOT_VERIFIED"})
        if account_id in store.blocked_payment_push:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "ESCALATED_NO_PAYMENT_PUSH"})
        acct = store.accounts.get(account_id)
        if acct is None:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "UNKNOWN_ACCOUNT"})
        if acct["status"] == "PAID" or acct["outstanding"] <= 0:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "ACCOUNT_ALREADY_PAID"})
        parsed_amount = _parse_amount(amount)
        if parsed_amount is None:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "INVALID_AMOUNT"})
        if parsed_amount < acct["minimum_due"]:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "BELOW_MINIMUM_DUE"})
        if parsed_amount > acct["outstanding"]:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "ABOVE_OUTSTANDING"})
        today = store.now.astimezone(IST).date()
        parsed_date = _parse_date(pay_date, today)
        if parsed_date is None:
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "INVALID_DATE"})
        if parsed_date < today or parsed_date > today + timedelta(days=7):
            return store.log("record_promise_to_pay", args, {"ok": False, "error": "DATE_OUT_OF_WINDOW"})
        record = {
            "account_id": account_id,
            "amount": parsed_amount,
            "pay_date": parsed_date.isoformat(),
        }
        store.ptps.append(record)
        return store.log("record_promise_to_pay", args, {"ok": True, **{**record, "amount": str(parsed_amount)}})

    @tool
    def schedule_callback(account_id: str, when: str) -> dict[str, Any]:
        """Book a callback. when is ISO datetime in IST. Only 08:00-19:00 IST. Requires verified identity."""
        args = {"account_id": account_id, "when": when}
        if account_id not in store.verified:
            return store.log("schedule_callback", args, {"ok": False, "error": "IDENTITY_NOT_VERIFIED"})
        if account_id not in store.accounts:
            return store.log("schedule_callback", args, {"ok": False, "error": "UNKNOWN_ACCOUNT"})
        parsed = _parse_when(when, store.now)
        if parsed is None:
            return store.log("schedule_callback", args, {"ok": False, "error": "INVALID_DATETIME"})
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        local = parsed.astimezone(IST)
        if local.time() < CALL_START or local.time() > CALL_END:
            return store.log("schedule_callback", args, {"ok": False, "error": "OUTSIDE_CALLBACK_HOURS"})
        rec = {"account_id": account_id, "when": local.isoformat()}
        store.callbacks.append(rec)
        return store.log("schedule_callback", args, {"ok": True, **rec})

    @tool
    def escalate_to_human(account_id: str, reason: str, notes: str) -> dict[str, Any]:
        """Hand off to a human. Use for DISPUTE, ALREADY_PAID, HARDSHIP, ABUSE, WRONG_PERSON. Never push payment after this."""
        args = {"account_id": account_id, "reason": reason, "notes": notes}
        reason_u = (reason or "OTHER").upper()
        if reason_u not in ESCALATE_REASONS:
            reason_u = "OTHER"
        rec = {"account_id": account_id, "reason": reason_u, "notes": notes}
        store.escalations.append(rec)
        if reason_u in {"DISPUTE", "ALREADY_PAID", "HARDSHIP", "ABUSE"}:
            store.blocked_payment_push.add(account_id)
        return store.log("escalate_to_human", args, {"ok": True, **rec})

    return [
        verify_identity,
        get_account,
        record_promise_to_pay,
        schedule_callback,
        escalate_to_human,
    ]


def tool_map(store: Store) -> dict[str, Any]:
    return {t.name: t for t in build_tools(store)}
