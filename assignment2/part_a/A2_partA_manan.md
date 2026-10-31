# Assignment 2, Part A — Dialer Campaign Analytics

## A1. Capacity planning

**Per account (attempts stop once connected, max 3, p = 0.25, q = 0.75):**

| | Formula | Value |
|---|---|---|
| Expected attempts | 1 + q + q² = 1 + 0.75 + 0.5625 | **2.3125** |
| P(connected at some point) | 1 − q³ = 1 − 0.421875 | **0.578125** |
| Expected unanswered attempts | 2.3125 − 0.578125 | **1.734375** |
| Line-seconds per account | 0.578125 × 120 + 1.734375 × 30 = 69.375 + 52.031 | **≈ 121.4 s** |

(Attempt 2 happens only if attempt 1 failed, probability 0.75; attempt 3 only if both failed, 0.75².)

**Whole day:**

- Total line-seconds = 200,000 × 121.4 ≈ **24.28 million s**
- Calling day = 10 h × 3,600 = **36,000 s**
- Average concurrent lines = 24,281,250 ÷ 36,000 ≈ **675 lines**

**What I'd add for safety → plan for ~800 lines (≈ +20%):**

- **Load isn't flat.** 675 is an average. Connect rates are higher at certain hours (10–12, evenings), so connected calls (4× longer) cluster. Calls arrive randomly too: with ~675 Erlangs, one standard deviation is √675 ≈ 26 lines, so covering 3σ needs ≈ 750.
- **The 60-minute retry gap and calling-hours windows** squeeze attempts 2 and 3 into the later part of the day, and borrowers in different time zones can only be called in their own 08:00–19:00, so the first and last hours are uneven.
- **Overheads not in the model:** dial/ring setup, carrier failures, wrap-up time, and lines down for maintenance.
- **Average handle time is an estimate.** If connected calls average 150 s instead of 120 s, load rises by about 14%.

## A2. A/B test

| Script | Connected | PTP | PTP rate | Kept PTPs | Kept per connected call |
|---|---|---|---|---|---|
| A | 4,000 | 880 | 22.0% | 880 × 0.60 = **528** | **13.2%** |
| B | 4,000 | 960 | 24.0% | 960 × 0.50 = **480** | **12.0%** |

**Test: two-proportion z-test on PTP rate.** H₀: p_B = p_A; H₁: p_B > p_A.

- Pooled p = (880 + 960) ÷ 8,000 = 0.23
- SE = √(0.23 × 0.77 × (1/4000 + 1/4000)) = **0.00941**
- z = (0.24 − 0.22) ÷ 0.00941 = **2.13**
- One-sided p ≈ 0.017 (two-sided ≈ 0.034). Critical value 1.645 (one-sided) / 1.96 (two-sided).

→ **Yes, B's PTP rate is significantly higher at 95%.**

**But promises aren't money.** Same test on *kept promises per connected call*:

- Pooled p = (528 + 480) ÷ 8,000 = 0.126; SE = 0.00742
- z = (0.120 − 0.132) ÷ 0.00742 = **−1.62**, two-sided p ≈ 0.11

→ A collects **48 more kept promises per 4,000 connected calls** (~9% more), but this difference is **not significant** at 95%.

**Recommendation: do not roll out B; keep A.**

- B gets more people to say yes but fewer of them pay. That looks like softer, less committed promises, and they also cost follow-up effort and inflate the PTP metric.
- The business goal is cash collected, and on that measure A is ahead (not significantly yet).
- Next step: run longer, with **amount collected per connected call** as the primary metric. Also check PTP amounts (B's promises could be bigger or smaller) and that both arms had the same time to mature their kept/not-kept status.

## A3. Funnel diagnosis

| Week | Connect ÷ Dialed | **RPC ÷ Connected** | PTP ÷ RPC | Paid ÷ PTP | Paid ÷ Dialed |
|---|---|---|---|---|---|
| W1 | 25.0% | **80.0%** | 25.0% | 60.0% | 3.0% |
| W2 | 24.8% | **59.7%** | 29.7% | 59.1% | 2.6% |
| W3 | 25.0% | **57.7%** | 30.0% | 60.0% | 2.6% |

**Where it broke:** between **Connected and RPC**, starting W2 and not recovering in W3. We're still getting through at the same rate, but about 1 in 5 connected calls that used to reach the borrower now reach someone else. Every other step is flat. PTP ÷ RPC actually rises, but the PTP *count* still falls (2,500 → ~2,200), so overall paid per dialed is down from 3.0% to 2.6%, about **13% less cash per dial**.

**Hypotheses and the first data cut for each:**

1. **Bad contact data in a new allocation.** A new batch or lender upload in W2 has stale or wrong phone numbers.
   *Cut:* RPC ÷ connected and WRONG_NUMBER share **by batch / upload date × state**, W1 vs W2. One segment collapsing points here.
2. **Dialing pattern changed.** Different hours or days (more evening/weekend calls reach family members), or a new caller ID / dialer setting.
   *Cut:* RPC ÷ connected **by hour of day and weekday**, W1 vs W2, plus the dialer config change log.
3. **Disposition coding changed.** New agents or team, or a QA rule change, so calls that reach the borrower are now tagged as non-RPC.
   *Cut:* RPC ÷ connected **by agent / team**, plus a sample of W2 call recordings marked non-RPC to listen to.

## A4. Scheduler design

**Per-account state:** `tz`, `priority = dpd × outstanding`, `attempts_today`, `last_attempt_at`, `callback_at` (nullable), `local_day` (for resetting the counter).

**Data structures:**

- `waiting`: **min-heap** keyed by `next_eligible_at` (UTC). Holds accounts that can't be called yet (60-min gap, callback time, outside 08:00–19:00).
- `ready`: **max-heap** keyed by `(callback_due, priority)`. Holds accounts callable right now; due callbacks always come first.
- `accounts`: hash map `account_id → state`.

All times are stored in UTC; local time is only used for the window check.

```text
function next_eligible_at(acc, now):
    t = now
    if acc.last_attempt_at is set:
        t = max(t, acc.last_attempt_at + 60 min)
    if acc.callback_at is set and acc.callback_at > t:
        t = acc.callback_at                       # honour requested time
    local = to_local(t, acc.tz)
    if local.time < 08:00:
        t = at_local(local.date, 08:00, acc.tz)
    else if local.time >= 19:00:
        t = at_local(local.date + 1 day, 08:00, acc.tz)   # tomorrow, counter resets
    return t

function schedule(acc, now):
    push waiting (next_eligible_at(acc, now), acc.id)

function get_next_account(now):                   # called when a line frees up
    while waiting not empty and waiting.top.time <= now:
        acc = accounts[pop(waiting).id]
        reset_counter_if_new_local_day(acc, now)
        if acc.attempts_today >= 3:
            schedule for tomorrow 08:00 local; continue
        callback_due = acc.callback_at is set and acc.callback_at <= now
        push ready ((callback_due, acc.priority), acc.id)

    while ready not empty:
        acc = accounts[pop(ready).id]
        if not in_window(now, acc.tz) or acc.attempts_today >= 3:
            schedule(acc, now); continue          # stale entry, put it back
        return acc                                # popped, so no other line gets it
    return None                                   # all lines idle until waiting.top.time

function on_call_end(acc, outcome, now, requested_callback = null):
    acc.attempts_today += 1
    acc.last_attempt_at = now
    acc.callback_at = null
    if outcome in {PTP, PAID, DISPUTE, DO_NOT_CALL}:
        return                                    # done; handled outside the dialer
    if requested_callback:
        acc.callback_at = requested_callback
    schedule(acc, now)
```

**Assumptions and edge cases:**

- A requested callback still counts as an attempt and still has to fall inside 08:00–19:00 local. If the borrower asks for 21:00, compliance wins and we call at the next allowed time.
- `next_eligible_at` handles a callback falling inside the 60-minute gap by taking the later of the two.
- The dispatcher pops an account before handing it to a line, so two lines can't dial the same account. With several dispatcher workers, put a lock around the heaps or give each worker its own shard.
- Priority is fixed for the day. If outstanding changes (for example after a payment), re-push the account and skip outdated heap entries when they're popped.

**Complexity (n accounts):**

- Push and pop on either heap: **O(log n)**.
- Each account is pushed a bounded number of times per day (≤ 3 attempts plus window moves), so a full day is **O(n log n)**.
- `get_next_account` is **O(log n) amortised**: each account moves from `waiting` to `ready` once per attempt.
- Memory: **O(n)**.