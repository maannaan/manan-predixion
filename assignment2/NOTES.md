# Assignment 2 — notes

## Method

- Generator is copied from the brief and not modified (`numpy` default_rng 42, N=20,000).
- Connect = disposition ≠ `NO_ANSWER`.
- RPC = `PTP` or `RPC_NO_PTP`. PTP rate = PTP ÷ RPC.
- Weekend = `called_at.dayofweek >= 5`.
- DPD bands: 1–30, 31–60, 61–90, 91–120.
- Rates are unweighted binomial proportions on this extract.

## Findings (seed 42 run)

- 70,235 attempts. Connect 25.7%. Weekend 29.3% vs weekday 23.8%.
- Hour 18 peak (33.6%); midday trough ~21%.
- PTP/RPC 28.1% (DPD 1–30) vs 19.2% (91–120).
- PTP kept 64.9% at 1–5 days vs 34.4% at 6–14.
- Anomaly: batch B7 × state BR wrong-number rate 53.5% vs 7.8% elsewhere (114 lost RPCs).

## Tests

3 passed: generator freeze, planted effects, reproducibility of account ids.
