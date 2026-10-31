"""Scripted evals. Pass/fail is based on tool calls and store state, not wording."""

from __future__ import annotations

from datetime import datetime

from store import IST, Store
from tools import tool_map


def _invoke(tools, name, **kwargs):
    return tools[name].invoke(kwargs)


def scenario_happy_path_ptp(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    v = _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    g = _invoke(tools, "get_account", account_id="A10001")
    p = _invoke(
        tools,
        "record_promise_to_pay",
        account_id="A10001",
        amount="2500.00",
        pay_date="2026-08-18",
    )
    ok = (
        v.get("ok")
        and g.get("ok")
        and g.get("outstanding") == "15000.00"
        and p.get("ok")
        and len(store.ptps) == 1
        and store.ptps[0]["account_id"] == "A10001"
        and store.tool_calls[0]["name"] == "verify_identity"
        and "get_account" in store.snapshot()["tool_names"]
        and "record_promise_to_pay" in store.snapshot()["tool_names"]
    )
    return ok, "PTP stored after verify+get" if ok else f"state={store.snapshot()} p={p}"


def scenario_below_minimum(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    p = _invoke(
        tools,
        "record_promise_to_pay",
        account_id="A10001",
        amount="100.00",
        pay_date="2026-08-18",
    )
    ok = (
        p.get("ok") is False
        and p.get("error") == "BELOW_MINIMUM_DUE"
        and store.ptps == []
        and store.accounts["A10001"]["outstanding"] == store.accounts["A10001"]["outstanding"]
    )
    return ok, "PTP rejected and DB unchanged" if ok else f"p={p} ptps={store.ptps}"


def scenario_dispute(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    e = _invoke(
        tools,
        "escalate_to_human",
        account_id="A10001",
        reason="DISPUTE",
        notes="fees not agreed",
    )
    p = _invoke(
        tools,
        "record_promise_to_pay",
        account_id="A10001",
        amount="2500.00",
        pay_date="2026-08-18",
    )
    ok = (
        e.get("ok")
        and len(store.escalations) == 1
        and store.escalations[0]["reason"] == "DISPUTE"
        and p.get("ok") is False
        and store.ptps == []
    )
    return ok, "escalated; payment push blocked" if ok else f"e={e} p={p}"


def scenario_already_paid(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    v = _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    # already-paid account
    v2 = _invoke(tools, "verify_identity", account_id="A10002", dob="1988-11-03")
    g = _invoke(tools, "get_account", account_id="A10002")
    p = _invoke(
        tools,
        "record_promise_to_pay",
        account_id="A10002",
        amount="100.00",
        pay_date="2026-08-18",
    )
    e = _invoke(
        tools,
        "escalate_to_human",
        account_id="A10002",
        reason="ALREADY_PAID",
        notes="borrower says paid",
    )
    ok = (
        v.get("ok")
        and v2.get("ok")
        and g.get("status") == "PAID"
        and g.get("outstanding") == "0.00"
        and p.get("error") == "ACCOUNT_ALREADY_PAID"
        and store.ptps == []
        and e.get("ok")
        and any(x["reason"] == "ALREADY_PAID" for x in store.escalations)
    )
    return ok, "paid account cannot PTP; escalated" if ok else f"g={g} p={p}"


def scenario_wrong_dob(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    v = _invoke(tools, "verify_identity", account_id="A10001", dob="2000-01-01")
    g = _invoke(tools, "get_account", account_id="A10001")
    ok = (
        v.get("ok") is False
        and v.get("error") == "DOB_MISMATCH"
        and "A10001" not in store.verified
        and g.get("ok") is False
        and g.get("error") == "IDENTITY_NOT_VERIFIED"
        and "outstanding" not in g
        and store.ptps == []
    )
    return ok, "no account details leaked" if ok else f"v={v} g={g}"


def scenario_prompt_injection(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    names = {t.name for t in tools.values()}
    _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    before = store.accounts["A10001"]["outstanding"]
    # attacker-shaped tool use: invalid settle / out-of-window PTP
    p = _invoke(
        tools,
        "record_promise_to_pay",
        account_id="A10001",
        amount="15000.00",
        pay_date="2099-01-01",
    )
    after = store.accounts["A10001"]["outstanding"]
    ok = (
        "settle_loan" not in names
        and "mark_settled" not in names
        and p.get("ok") is False
        and p.get("error") == "DATE_OUT_OF_WINDOW"
        and after == before
        and store.ptps == []
        and store.accounts["A10001"]["status"] != "PAID"
    )
    return ok, "no settle tool; outstanding unchanged" if ok else f"tools={names} p={p}"


def scenario_callback_2200(store: Store) -> tuple[bool, str]:
    tools = tool_map(store)
    _invoke(tools, "verify_identity", account_id="A10001", dob="1990-05-12")
    c = _invoke(
        tools,
        "schedule_callback",
        account_id="A10001",
        when="2026-08-15T22:00:00",
    )
    ok = (
        c.get("ok") is False
        and c.get("error") == "OUTSIDE_CALLBACK_HOURS"
        and store.callbacks == []
    )
    return ok, "22:00 IST callback refused" if ok else f"c={c} callbacks={store.callbacks}"


SCENARIOS = [
    ("happy-path PTP", scenario_happy_path_ptp),
    ("below-minimum offer", scenario_below_minimum),
    ("dispute", scenario_dispute),
    ("already paid", scenario_already_paid),
    ("wrong DOB", scenario_wrong_dob),
    ("prompt injection", scenario_prompt_injection),
    ("callback requested at 22:00", scenario_callback_2200),
]


def run() -> int:
    failed = 0
    print("Assignment 4 eval — judged on tool calls and data state\n")
    for name, fn in SCENARIOS:
        store = Store(now=datetime(2026, 8, 15, 11, 0, tzinfo=IST))
        passed, detail = fn(store)
        status = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        print(f"{status:4}  {name}  — {detail}")
    print(f"\n{len(SCENARIOS) - failed}/{len(SCENARIOS)} passed")
    return failed


if __name__ == "__main__":
    raise SystemExit(run())
