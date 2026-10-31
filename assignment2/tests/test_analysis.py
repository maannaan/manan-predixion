from pathlib import Path

import pandas as pd

from analyze import compute_metrics, enrich, ensure_data

ROOT = Path(__file__).resolve().parents[1]


def test_generator_script_not_modified():
    src = (ROOT / "gen_data.py").read_text(encoding="utf-8")
    assert "default_rng(42)" in src
    assert "N = 20_000" in src
    assert '["MH","KA","TN","UP","BR","GJ"]' in src
    assert '(batch == "B7") & (state == "BR")' in src


def test_dataset_shape_and_planted_effects():
    accounts, calls = ensure_data()
    assert len(accounts) == 20_000
    assert len(calls) > 20_000
    df = enrich(accounts, calls)
    m = compute_metrics(df)

    assert m["connect_weekend"] > m["connect_weekday"]
    assert m["connect_by_hour"].loc[10] > m["connect_by_hour"].loc[8]
    assert m["connect_by_hour"].loc[17] > m["connect_by_hour"].loc[8]

    assert 0.45 <= m["b7br_wrong_rate"] <= 0.65
    assert m["b7br_wrong_rate"] > m["rest_wrong_rate"] * 3
    assert str(m["top_segment"]["segment"]).replace(" ", "") in {"BR×B7", "B7×BR"} or (
        "B7" in str(m["top_segment"]["segment"]) and "BR" in str(m["top_segment"]["segment"])
    )

    kept = m["kept_window"]
    assert float(kept.loc["1–5 days", "mean"]) > float(kept.loc["6–14 days", "mean"])

    ptp = m["ptp_by_dpd"]
    assert float(ptp.iloc[0]) > float(ptp.iloc[-1])


def test_csv_reproducible_with_seed():
    accounts, _ = ensure_data()
    assert accounts.loc[0, "account_id"] == "A00000"
    assert set(accounts["state"].unique()) <= {"MH", "KA", "TN", "UP", "BR", "GJ"}
