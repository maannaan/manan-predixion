# Part A — Collections Ledger

## A1. Merge promise windows

**Approach:** sort windows by start day, then walk them once. If the next window starts on or before the current window's end, extend the end (`max`, to handle contained windows like `[1,10]` + `[2,3]`); otherwise start a new window.

- "Touching" means sharing a day: `[1,3]` + `[3,5]` → `[1,5]`.
- Adjacent days (`[1,4]`, `[5,8]`) stay separate, matching the example output.

**Complexity:** O(n log n) time (sort dominates; merge pass is O(n)). O(n) space for the sorted copy and output.

## A2. Excess call attempts

**Approach:** group timestamps by borrower, sort each list, then slide a window of `limit` consecutive attempts and check `times[i + limit - 1] - times[i] < window`.

**Why consecutive is enough:** if any `limit` attempts fit inside the window, then `limit` consecutive attempts in sorted order fit too — they are the tightest possible group.

- The comparison is strict: a span of exactly `window` seconds is not flagged.

**Complexity:** O(k log k) per borrower with k attempts (vs O(k²) for checking all pairs), O(n log n) overall. O(n) space.

**Streaming variant (if input is already sorted / live):** keep a deque per borrower, pop entries older than `now - window`, flag when the deque length reaches `limit`. O(1) amortised per call.

## A3. SQL

Queries are in `A1_partA_manan.sql`. Notes:

1. **DPD buckets** — buckets come from a `VALUES` table with a `LEFT JOIN`, so empty buckets still return 0 and the order is fixed.
2. **No recent contact** — `NOT EXISTS` anti-join (NULL-safe, unlike `NOT IN`).
3. **Latest payment + gap** — `ROW_NUMBER()` picks the latest payment per borrower; `LAG()` gives the previous `paid_at`. Ties broken by `payment_id`. A borrower with only one payment gets a NULL gap. Alternative: `DISTINCT ON (borrower_id)`.

"Today" is `CURRENT_DATE` / `now()` in the session time zone; in production I'd pin it to `Asia/Kolkata`.

### A3.4 Duplicate concurrent webhook

**What goes wrong:** two deliveries of the same webhook both check "already posted?", both see no, and both insert. Outstanding is reduced twice. If the balance update is read-then-write (`SELECT outstanding` → compute in app → `UPDATE`), concurrent updates can also overwrite each other (lost update). Result: double-counted collections and a wrong balance.

**Prevention at the database level:**

- `UNIQUE (gateway_txn_id)` on `payments` — the idempotency key; only one insert can succeed.
- In one transaction: `INSERT ... ON CONFLICT (gateway_txn_id) DO NOTHING RETURNING payment_id`. Zero rows returned → duplicate → stop without touching the balance.
- Reduce the balance atomically: `UPDATE loans SET outstanding_amount = GREATEST(outstanding_amount - $amount, 0) WHERE loan_id = $id`. The row lock serialises concurrent payments to the same loan.
- Backstop constraints: `CHECK (amount > 0)`, `CHECK (outstanding_amount >= 0)`.

**Indexes:**

- Query 2: partial index `call_logs (loan_id, called_at DESC) WHERE disposition IN ('CONNECTED','PTP','DISPUTE')`; partial index `loans (due_date) WHERE outstanding_amount > 0`.
- Query 3: `payments (loan_id, paid_at, payment_id)` and `loans (borrower_id)` — Postgres does not index foreign keys automatically.