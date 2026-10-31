# Assignment 1 — Collections Ledger (Part B)

SQLite-backed `ledger/` package. Money is integer paise. Return values are exactly `POSTED`, `DUPLICATE`, `OVERPAID`.

## Layout

- `part_a/` — independent Part A (`merge_windows`, `flag_excess_attempts`, SQL). Not edited by AI.
- `ledger/` — Part B package. Idempotency matches Part A A3.4 (`UNIQUE gateway_txn_id`).
- `tests/` — pytest (ledger + Part A helpers)

## API

| Function | Behavior |
|---|---|
| `init_db(path)` | Creates `loans` and `payments` with constraints; returns a connection |
| `post_payment(conn, loan_id, amount, gateway_txn_id) -> str` | Atomic + idempotent on `gateway_txn_id` |
| `collection_efficiency(conn, year, month) -> float` | Collected in month ÷ EMI due in month |
| `load_loans_csv(conn, path)` | Inserts valid rows; returns `[{"line", "reason"}, ...]` |

`post_payment` amounts are rupees as `Decimal`, `int`, or numeric `str` (not `float`).

CSV header: `loan_id,emi_amount,outstanding_amount,due_date` with `due_date` as `YYYY-MM-DD`.

## Run tests

```bash
cd assignment1
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Expected: ledger tests plus Part A helper tests.
