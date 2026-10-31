# Assignment 2, Part A — Dialer Campaign Analytics

## A1. Capacity Planning

**Per Account (Maximum 3 Attempts)**

Given:
- Connection probability (p) = 0.25
- Failure probability (q) = 0.75

| Metric | Formula | Result |
|---|---|---|
| Expected attempts | 1 + q + q² | 2.3125 |
| Connection probability | 1 - q³ | 57.81% |
| Unanswered attempts | 2.3125 - 0.578125 | 1.734375 |
| Line time per account | (0.578125 × 120) + (1.734375 × 30) | 121.4 seconds |

**Daily Capacity:**

- Total line time = 200,000 × 121.4 = 24.28 million seconds.
- Calling hours = 10 × 3,600 = 36,000 seconds.
- Required concurrent lines = 24.28 million / 36,000.
- Average requirement = **675 lines**.

**Recommended Capacity: 800 Lines**

I would keep around 20% extra capacity because:

- Call volume is not the same throughout the day.
- Connected calls take longer and can increase peak usage.
- The 60-minute retry gap affects when the next attempts happen.
- Different borrower time zones create uneven calling hours.
- Dialing delays, carrier issues and maintenance also need to be considered.
- If connected calls take 150 seconds instead of 120, capacity requirements increase.

## A2. A/B Test

| Script | Connected | PTP | PTP Rate | Kept PTPs | Kept Rate |
|---|---:|---:|---:|---:|---:|
| A | 4,000 | 880 | 22% | 528 | 13.2% |
| B | 4,000 | 960 | 24% | 480 | 12% |

**Statistical Test:**

I used a two-proportion z-test to compare the PTP rates.

- H0: Both scripts have the same PTP rate.
- H1: Script B has a higher PTP rate.
- Pooled rate = 0.23
- Standard error = 0.00941
- Z-score = 2.13
- One-sided p-value ≈ 0.017

**Result:** Script B has a significantly higher PTP rate at the 95% confidence level.

However, looking at kept promises:

- Script A: 528 kept promises.
- Script B: 480 kept promises.
- Difference: 48 more kept promises for A.

This difference is not statistically significant at the 95% level (z = -1.62, p ≈ 0.11).

**Recommendation:**

I would continue with Script A for now.

Script B gets more people to make promises, but fewer of those promises are kept. I would run the test for a longer period and use actual amount collected per connected call as the main metric.

## A3. Funnel Diagnosis

| Week | Connect / Dialed | RPC / Connected | PTP / RPC | Paid / PTP | Paid / Dialed |
|---|---:|---:|---:|---:|---:|
| W1 | 25.0% | 80.0% | 25.0% | 60.0% | 3.0% |
| W2 | 24.8% | 59.7% | 29.7% | 59.1% | 2.6% |
| W3 | 25.0% | 57.7% | 30.0% | 60.0% | 2.6% |

**Main Finding:**

The biggest drop is between Connected and RPC, starting from W2.

The connection rate is almost unchanged, but fewer calls are reaching the actual borrower.

As a result, the overall paid-to-dialed rate dropped from 3.0% to 2.6%.

**Possible Reasons and Checks:**

1. **Incorrect Contact Details**

   A new borrower allocation may contain outdated or incorrect phone numbers.

   Check RPC rate and WRONG_NUMBER records by batch, upload date and state.

2. **Changes in Calling Patterns**

   Calling hours, weekdays or caller ID settings may have changed.

   Compare RPC rates by hour and weekday. Also check dialer configuration changes.

3. **Disposition Coding Changes**

   Agents may be using different call dispositions after a process or team change.

   Compare results by agent and team. Review recordings of calls marked as non-RPC.

## A4. Scheduler Design

**Account Details:**

Each account will store:

- `tz` – Borrower's timezone.
- `priority` – DPD × outstanding amount.
- `attempts_today` – Number of attempts made today.
- `last_attempt_at` – Last call time.
- `callback_at` – Requested callback time.
- `local_day` – Used to reset the daily attempt count.

**Data Structures:**

- `waiting`: Min-heap for accounts that are not ready to call.
- `ready`: Max-heap for accounts that can be called.
- `accounts`: Hash map storing account details.

All timestamps are stored in UTC. Local time is used only for checking calling hours.

### Scheduler Logic

```text
function next_eligible_at(acc, now):
    t = now

    if acc.last_attempt_at exists:
        t = max(t, acc.last_attempt_at + 60 minutes)

    if acc.callback_at exists:
        t = max(t, acc.callback_at)

    local = convert_to_local(t, acc.tz)

    if local.time < 08:00:
        t = next_allowed_time(local.date, 08:00, acc.tz)

    else if local.time >= 19:00:
        t = next_day_at_08:00(acc.tz)

    return t


function schedule(acc, now):
    push waiting(next_eligible_at(acc, now), acc.id)


function get_next_account(now):

    while waiting is not empty and waiting.top.time <= now:

        acc = accounts[pop(waiting).id]

        reset_counter_if_new_day(acc, now)

        if acc.attempts_today >= 3:
            schedule_for_tomorrow(acc)
            continue

        callback_due = acc.callback_at exists
                       and acc.callback_at <= now

        push ready(callback_due, acc.priority, acc.id)

    while ready is not empty:

        acc = pop(ready)

        if not in_calling_window(acc, now):
            schedule(acc, now)
            continue

        if acc.attempts_today >= 3:
            continue

        return acc

    return None


function on_call_end(acc, outcome, now, requested_callback = null):

    acc.attempts_today += 1
    acc.last_attempt_at = now
    acc.callback_at = null

    if outcome in {PTP, PAID, DISPUTE, DO_NOT_CALL}:
        return

    if requested_callback exists:
        acc.callback_at = requested_callback

    schedule(acc, now)