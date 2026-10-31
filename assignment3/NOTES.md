# Assignment 3 — notes

## Part A → Part B

`app/retry.py` imports `schedule_retry`, `notify_crm`, and `RETRYABLE` from `part_a/A3_partA_manan.py`. Window is 08:00 inclusive, 19:00 exclusive. Negative attempt raises `ValueError`. CRM notify is async with backoff; webhook still returns 200 if CRM is down.

## Part B decisions

- IST via `ZoneInfo("Asia/Kolkata")`. After 19:00 IST, next slot is 08:00 next day (not 09:00). Before 08:00, same-day 08:00. 07:30+30m = 08:00.
- `disposition in {"NO_ANSWER", "BUSY"}` — the original `or "BUSY"` was always true.
- Unique `gateway` equivalent here is parameterized SQL + no shared naive `datetime.now()`.
- Task execution role reads the secret; task role is empty (no AWS API from the app).
- Deploy apply is opt-in so CI cannot spend money by default.

## Evidence

See `EVIDENCE.md` after local docker/terraform commands are run.
