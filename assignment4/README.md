# Assignment 4 — Collections Assistant Agent (Part B)

Text-mode collections agent. Rules live in **tool code**. Evals judge **tool calls and mock DB state**, not wording.

**Part B loads the rewritten system prompt from `part_a/A4_partA_manan.md`.** Tools still enforce the rules in code. Do not edit Part A from the assistant.

## Layout

- `store.py` — in-memory accounts, PTPs, callbacks, escalations, tool-call log
- `tools.py` — five tools with enforcement
- `agent.py` — LangGraph `create_react_agent`, system prompt, thread memory (`MemorySaver`)
- `eval.py` — seven scripted scenarios

Seeded accounts: `A10001` overdue (DOB `1990-05-12`), `A10002` fully paid (DOB `1988-11-03`). Clock for evals: 2026-08-15 11:00 IST.

## Run

```bash
cd assignment4
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python eval.py
pytest
```

Optional live agent (needs `OPENAI_API_KEY`): `python agent.py`

## What is enforced in tools (not only the prompt)

| Rule | Where |
|---|---|
| No account details before identity | `get_account` / PTP / callback require `verify_identity` |
| DOB must match | `verify_identity` |
| PTP date today..today+7 | `record_promise_to_pay` |
| PTP amount in [minimum due, outstanding] | `record_promise_to_pay` |
| Paid accounts cannot PTP | `record_promise_to_pay` |
| Callbacks 08:00–19:00 IST | `schedule_callback` |
| Dispute / hardship / abuse / claimed payment | `escalate_to_human` then PTP blocked |
| No settle / mark-paid tool | tool list |

Prompt additionally forbids threats, legal/police/family language, and instruction override.

## Evals (7/7)

happy-path PTP · below-minimum offer · dispute · already paid · wrong DOB · prompt injection · callback at 22:00

## Failure modes

- Without an API key the LLM loop is not run; evals still exercise tools and state.
- A live model can still say the wrong thing; tools will refuse invalid mutations.
- Identity is per in-memory session, not a real KYC vendor.
