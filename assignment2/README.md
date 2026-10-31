# Assignment 2 — Dialer Campaign Analytics (Part B)

## Layout

- `part_a/` — your independent Part A work. Not generated or edited by AI.
- `gen_data.py` — **exact** generator from the brief. Do not modify.
- `analyze.py` — metrics, charts, memo
- `analysis.ipynb` — same analysis as a notebook
- `MEMO.md` — one-page note to the Collections Head
- `charts/` — PNG figures

## Run

```bash
cd assignment2
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gen_data.py
python analyze.py
pytest
```

`accounts.csv` / `calls.csv` are generated locally and are gitignored. Re-run `gen_data.py` (seed 42) for a bit-identical extract.
