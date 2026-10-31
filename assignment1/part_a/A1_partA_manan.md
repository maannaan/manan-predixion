# Part A — Collections Ledger

## A1. Merge Promise Windows

**Approach:**

Sort windows by their start day and compare each window with the previous one.

If the next window starts on or before the current ending day, merge them and keep the maximum ending day. Otherwise, keep them separate.

- `[1,3]` + `[3,5]` → `[1,5]`
- `[1,4]` + `[5,8]` → Remain separate.

**Complexity:** O(n log n) time and O(n) space.

## A2. Excess Call Attempts

**Approach:**

Group timestamps by borrower ID and sort them. Use a sliding window to check every group of `limit` consecutive calls.

If the difference between the first and last call is less than the given time window, flag the borrower.

A difference exactly equal to the window is not flagged.

**Complexity:** O(n log n) time and O(n) space.

For live calls, a deque can be used to remove older timestamps and check the limit in O(1) amortised time per call.

## A3. SQL Queries

All queries are available in `A1_partA_manan.sql`.

1. **DPD Buckets:** Used `VALUES` with `LEFT JOIN` so empty buckets also appear with a count of 0.
2. **No Recent Contact:** Used `NOT EXISTS` to find borrowers without recent contact. It also handles NULL values safely.
3. **Latest Payment:** Used `ROW_NUMBER()` to get the latest payment and `LAG()` to calculate the gap between payments. Ties are handled using `payment_id`.

The queries use the database session timezone. In production, I would set it to `Asia/Kolkata`.

### A3.4. Duplicate Concurrent Webhooks

**Problem:**

If the same webhook arrives twice at the same time, both requests may check for the payment before either inserts it. This can result in duplicate payments and an incorrect outstanding balance.

**Solution:**

- Add a `UNIQUE (gateway_txn_id)` constraint to prevent duplicate payments.
- Use `INSERT ... ON CONFLICT DO NOTHING RETURNING payment_id` inside a transaction.
- If no row is returned, stop processing because the payment already exists.
- Update the loan balance directly using an atomic SQL update:

```sql
UPDATE loans
SET outstanding_amount = GREATEST(outstanding_amount - $amount, 0)
WHERE loan_id = $id;