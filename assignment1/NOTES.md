# Assignment 1 — notes

## Part A → Part B

`post_payment` is the Part A A3.4 fix in code: `UNIQUE(gateway_txn_id)` plus `BEGIN IMMEDIATE`. `merge_windows` / `flag_excess_attempts` stay in `part_a/` and are covered by `tests/test_part_a.py`.

## Decisions

- Store rupees as integer paise. SQLite has no Decimal type; floats are forbidden for money.
- `BEGIN IMMEDIATE` plus `UNIQUE(gateway_txn_id)` makes `post_payment` atomic and idempotent under concurrent writers (WAL + busy timeout).
- Overpayment: insert the **full** amount, apply `min(amount, outstanding)`, record `excess_paise`, set outstanding to 0, return `OVERPAID`. Exact payoff returns `POSTED`.
- Duplicate `gateway_txn_id` returns `DUPLICATE` and does not change outstanding.
- EMI due in a month = sum of `emi_amount` for loans whose `due_date` falls in that calendar month. Collected = sum of payment `amount_paise` whose `paid_at` prefix matches `YYYY-MM`. If no EMI due, efficiency is `0.0`.

## Limitations

- One `due_date` per loan, so “EMI due in month” is not a full amortization schedule.
- SQLite, not PostgreSQL. Concurrency is serialised writers, which matches the 8-thread requirement.
- CSV schema is documented above; the brief did not specify column names.

## Tests

`pytest` in this folder: 9 passed (happy path, duplicate, exact payoff, overpay, invalid amount, unknown loan, 8-thread race, efficiency, CSV rejections).
