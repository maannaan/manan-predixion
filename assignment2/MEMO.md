# Memo: Dialer campaign — three quantified actions

To: Collections Head  
From: Analytics (campaign extract, Aug 2026, N=20,000 accounts, 70,235 attempts)  
Re: Connect, PTP quality, and one broken segment

## What the data shows

Overall connect rate is 25.7%. Connect is not flat through the day: 18:00 is 33.6% vs 12:00 at 21.2%. Weekends connect at 29.3% vs 23.8% on weekdays (+5.4 pp).

PTP / RPC declines with age: 28.1% in DPD 1–30 vs 19.2% in 91–120. Once a PTP is taken, keep-rate is 64.9% when the promise is 1–5 days (n=1,399) vs 34.4% at 6–14 days (n=2,493).

Wrong-number rate among connected calls is 7.8% everywhere except **batch B7 × state BR**, where it is 53.5% (n=213 connected). That cell produced 114 wrong-number connects that never became RPC.

Assumptions: rates are binomial proportions on this extract (no survey weights). Weekend = Saturday/Sunday (`dayofweek >= 5`). RPC = PTP or RPC_NO_PTP. PTP rate = PTP ÷ RPC, as specified. We did not change the data generator.

## Recommendations

1. **Quarantine B7 numbers in BR until the file is scrubbed.** Wrong-number rate is 45.7 pp above the rest of the book. Stopping those 213 connected attempts from burning as WRONG_NUMBER would recover about **114 RPCs** in a comparable 30-day window (or the same capacity reallocated to other batches/states at the ~92% RPC-given-connect rate). Do not add B7/BR volume until the number vendor is replaced.

2. **Move attempt share into 10:00–12:00 and 17:00–19:00, and staff weekend lines.** Peak-hour connect is 32.6% vs 21.7% in the remaining 08:00–19:00 slots (10.9 pp). About 64% of attempts sit in those weaker hours. Shifting them to peak slots is worth on the order of **4,900 additional connects** on this volume, before RPC conversion. Weekend already outperforms weekday by 5.4 pp; put overflow capacity there rather than more Monday-morning volume.

3. **Cap PTP dates at 5 days unless the borrower insists.** Keep-rate drops from 64.9% to 34.4% after day 5. On this extract, converting the 2,493 longer PTPs to the short-window keep-rate would yield about **760 extra kept PTPs**. Pair this with preferring lower-DPD RPC for PTP pitches (28.1% vs 19.2% PTP/RPC).

## What we are not claiming

Causal impact of a full re-roster needs an A/B (hour and weekend lifts are observational on the planted calling mix). B7×BR is large enough that a data-quality action should not wait for a test.
