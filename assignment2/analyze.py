"""Dialer campaign analysis. Does not modify gen_data.py."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"

DPD_BINS = [0, 30, 60, 90, 121]
DPD_LABELS = ["1–30", "31–60", "61–90", "91–120"]


def ensure_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        if not (ROOT / "accounts.csv").exists() or not (ROOT / "calls.csv").exists():
            runpy.run_path(str(ROOT / "gen_data.py"), run_name="__main__")
        accounts = pd.read_csv(ROOT / "accounts.csv")
        calls = pd.read_csv(ROOT / "calls.csv", parse_dates=["called_at"])
    finally:
        os.chdir(cwd)
    return accounts, calls


def enrich(accounts: pd.DataFrame, calls: pd.DataFrame) -> pd.DataFrame:
    df = calls.merge(accounts, on="account_id", how="left")
    df["hour"] = df["called_at"].dt.hour
    df["is_weekend"] = df["called_at"].dt.dayofweek >= 5
    df["connected"] = df["disposition"] != "NO_ANSWER"
    df["rpc"] = df["disposition"].isin(["PTP", "RPC_NO_PTP"])
    df["is_ptp"] = df["disposition"] == "PTP"
    df["wrong"] = df["disposition"] == "WRONG_NUMBER"
    df["dpd_band"] = pd.cut(df["dpd"], bins=DPD_BINS, labels=DPD_LABELS, right=True)
    return df


def connect_by_hour(df: pd.DataFrame) -> pd.Series:
    return df.groupby("hour")["connected"].mean().sort_index()


def connect_by_weekend(df: pd.DataFrame) -> pd.Series:
    out = df.groupby("is_weekend")["connected"].mean()
    out.index = out.index.map({False: "weekday", True: "weekend"})
    return out


def ptp_rate_by_dpd(df: pd.DataFrame) -> pd.Series:
    rpc = df[df["rpc"]]
    return rpc.groupby("dpd_band", observed=True)["is_ptp"].mean()


def ptp_kept_by_days(df: pd.DataFrame) -> pd.DataFrame:
    ptp = df[df["is_ptp"]].copy()
    ptp["days_to_promise"] = ptp["days_to_promise"].astype(int)
    ptp["ptp_kept"] = ptp["ptp_kept"].astype(bool)
    by_day = ptp.groupby("days_to_promise")["ptp_kept"].mean()
    ptp["window"] = pd.cut(
        ptp["days_to_promise"],
        bins=[0, 5, 15],
        labels=["1–5 days", "6–14 days"],
        right=True,
    )
    by_window = ptp.groupby("window", observed=True)["ptp_kept"].agg(["mean", "count"])
    return by_day, by_window


def anomalous_segments(df: pd.DataFrame) -> pd.DataFrame:
    connected = df[df["connected"]]
    rows = []
    for cols in (("state",), ("batch",), ("state", "batch")):
        g = connected.groupby(list(cols), observed=True).agg(
            n=("wrong", "size"),
            wrong_rate=("wrong", "mean"),
            rpc_rate=("rpc", "mean"),
        )
        g = g.reset_index()
        g["segment"] = g[list(cols)].astype(str).agg(" × ".join, axis=1)
        rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    overall = connected["wrong"].mean()
    out["lift_vs_overall"] = out["wrong_rate"] / overall
    return out.sort_values("wrong_rate", ascending=False)


def compute_metrics(df: pd.DataFrame) -> dict:
    by_hour = connect_by_hour(df)
    by_we = connect_by_weekend(df)
    ptp_dpd = ptp_rate_by_dpd(df)
    kept_day, kept_window = ptp_kept_by_days(df)
    segs = anomalous_segments(df)
    top = segs.iloc[0]

    connected = df[df["connected"]]
    b7br = connected[(connected["batch"] == "B7") & (connected["state"] == "BR")]
    rest = connected[~((connected["batch"] == "B7") & (connected["state"] == "BR"))]

    peak_hours = by_hour.loc[[10, 11, 17, 18]].mean() if set([10, 11, 17, 18]).issubset(by_hour.index) else by_hour.max()
    off_hours = by_hour.loc[[8, 9, 12, 13, 14, 15, 16]].mean()

    n_calls = len(df)
    n_peak_share = df["hour"].isin([10, 11, 17, 18]).mean()

    return {
        "n_calls": n_calls,
        "n_accounts": df["account_id"].nunique(),
        "connect_overall": float(df["connected"].mean()),
        "connect_by_hour": by_hour,
        "connect_weekday": float(by_we["weekday"]),
        "connect_weekend": float(by_we["weekend"]),
        "ptp_by_dpd": ptp_dpd,
        "kept_by_day": kept_day,
        "kept_window": kept_window,
        "top_segment": top,
        "segments": segs,
        "b7br_n": int(len(b7br)),
        "b7br_wrong_rate": float(b7br["wrong"].mean()) if len(b7br) else 0.0,
        "rest_wrong_rate": float(rest["wrong"].mean()) if len(rest) else 0.0,
        "b7br_lost_rpc": int(b7br["wrong"].sum()),
        "peak_connect": float(peak_hours),
        "off_connect": float(off_hours),
        "n_peak_share": float(n_peak_share),
        "n_off_share": float(1 - n_peak_share),
        "ptp_n": int(df["is_ptp"].sum()),
        "rpc_n": int(df["rpc"].sum()),
    }


def save_charts(df: pd.DataFrame, metrics: dict) -> None:
    CHARTS.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4))
    metrics["connect_by_hour"].plot(kind="bar", ax=ax, color="#1f4e79")
    ax.set_ylabel("Connect rate")
    ax.set_xlabel("Hour (borrower-local, 24h)")
    ax.set_title("Connect rate by hour of day")
    ax.set_ylim(0, 0.45)
    fig.tight_layout()
    fig.savefig(CHARTS / "connect_by_hour.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    pd.Series(
        {"weekday": metrics["connect_weekday"], "weekend": metrics["connect_weekend"]}
    ).plot(kind="bar", ax=ax, color=["#4a4a4a", "#1f4e79"])
    ax.set_ylabel("Connect rate")
    ax.set_title("Connect rate: weekday vs weekend")
    ax.set_ylim(0, 0.45)
    fig.tight_layout()
    fig.savefig(CHARTS / "connect_weekday_weekend.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    metrics["ptp_by_dpd"].plot(kind="bar", ax=ax, color="#1f4e79")
    ax.set_ylabel("PTP / RPC")
    ax.set_xlabel("DPD band")
    ax.set_title("PTP rate by DPD band")
    ax.set_ylim(0, 0.4)
    fig.tight_layout()
    fig.savefig(CHARTS / "ptp_by_dpd.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    metrics["kept_by_day"].plot(kind="bar", ax=ax, color="#1f4e79")
    ax.set_ylabel("PTP kept rate")
    ax.set_xlabel("Days to promise")
    ax.set_title("PTP kept rate by days-to-promise")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(CHARTS / "ptp_kept_by_days.png", dpi=120)
    plt.close(fig)

    pivot = (
        df[df["connected"]]
        .pivot_table(index="state", columns="batch", values="wrong", aggfunc="mean")
        .sort_index()
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(pivot.values, aspect="auto", cmap="Reds", vmin=0, vmax=0.6)
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title("Wrong-number rate among connected calls (state × batch)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(CHARTS / "wrong_rate_heatmap.png", dpi=120)
    plt.close(fig)


def write_memo(metrics: dict) -> str:
    hour = metrics["connect_by_hour"]
    kw = metrics["kept_window"]
    kept_short = float(kw.loc["1–5 days", "mean"])
    kept_long = float(kw.loc["6–14 days", "mean"])
    n_short = int(kw.loc["1–5 days", "count"])
    n_long = int(kw.loc["6–14 days", "count"])

    extra_connect = metrics["connect_weekend"] - metrics["connect_weekday"]
    peak_lift = metrics["peak_connect"] - metrics["off_connect"]
    extra_wrong = metrics["b7br_wrong_rate"] - metrics["rest_wrong_rate"]
    recovered = metrics["b7br_lost_rpc"]

    off_calls = metrics["n_calls"] * metrics["n_off_share"]
    extra_connects_if_shifted = off_calls * peak_lift

    ptp_dpd = metrics["ptp_by_dpd"]
    low_band = ptp_dpd.iloc[0]
    high_band = ptp_dpd.iloc[-1]

    memo = f"""# Memo: Dialer campaign — three quantified actions

To: Collections Head  
From: Analytics (campaign extract, Aug 2026, N={metrics["n_accounts"]:,} accounts, {metrics["n_calls"]:,} attempts)  
Re: Connect, PTP quality, and one broken segment

## What the data shows

Overall connect rate is {metrics["connect_overall"]:.1%}. Connect is not flat through the day: {hour.idxmax()}:00 is {hour.max():.1%} vs {hour.idxmin()}:00 at {hour.min():.1%}. Weekends connect at {metrics["connect_weekend"]:.1%} vs {metrics["connect_weekday"]:.1%} on weekdays (+{extra_connect * 100:.1f} pp).

PTP / RPC declines with age: {low_band:.1%} in DPD {ptp_dpd.index[0]} vs {high_band:.1%} in {ptp_dpd.index[-1]}. Once a PTP is taken, keep-rate is {kept_short:.1%} when the promise is 1–5 days (n={n_short:,}) vs {kept_long:.1%} at 6–14 days (n={n_long:,}).

Wrong-number rate among connected calls is {metrics["rest_wrong_rate"]:.1%} everywhere except **batch B7 × state BR**, where it is {metrics["b7br_wrong_rate"]:.1%} (n={metrics["b7br_n"]:,} connected). That cell produced {recovered:,} wrong-number connects that never became RPC.

Assumptions: rates are binomial proportions on this extract (no survey weights). Weekend = Saturday/Sunday (`dayofweek >= 5`). RPC = PTP or RPC_NO_PTP. PTP rate = PTP ÷ RPC, as specified. We did not change the data generator.

## Recommendations

1. **Quarantine B7 numbers in BR until the file is scrubbed.** Wrong-number rate is {extra_wrong * 100:.1f} pp above the rest of the book. Stopping those {metrics["b7br_n"]:,} connected attempts from burning as WRONG_NUMBER would recover about **{recovered:,} RPCs** in a comparable 30-day window (or the same capacity reallocated to other batches/states at the ~{1 - metrics["rest_wrong_rate"]:.0%} RPC-given-connect rate). Do not add B7/BR volume until the number vendor is replaced.

2. **Move attempt share into 10:00–12:00 and 17:00–19:00, and staff weekend lines.** Peak-hour connect is {metrics["peak_connect"]:.1%} vs {metrics["off_connect"]:.1%} in the remaining 08:00–19:00 slots ({peak_lift * 100:.1f} pp). About {metrics["n_off_share"]:.0%} of attempts sit in those weaker hours. Shifting them to peak slots is worth on the order of **{extra_connects_if_shifted:,.0f} additional connects** on this volume, before RPC conversion. Weekend already outperforms weekday by {extra_connect * 100:.1f} pp; put overflow capacity there rather than more Monday-morning volume.

3. **Cap PTP dates at 5 days unless the borrower insists.** Keep-rate drops from {kept_short:.1%} to {kept_long:.1%} after day 5. On this extract, converting the {n_long:,} longer PTPs to the short-window keep-rate would yield about **{(kept_short - kept_long) * n_long:,.0f} extra kept PTPs**. Pair this with preferring lower-DPD RPC for PTP pitches ({low_band:.1%} vs {high_band:.1%} PTP/RPC).

## What we are not claiming

Causal impact of a full re-roster needs an A/B (hour and weekend lifts are observational on the planted calling mix). B7×BR is large enough that a data-quality action should not wait for a test.
"""
    (ROOT / "MEMO.md").write_text(memo, encoding="utf-8")
    return memo


def main() -> dict:
    accounts, calls = ensure_data()
    df = enrich(accounts, calls)
    metrics = compute_metrics(df)
    save_charts(df, metrics)
    write_memo(metrics)
    return metrics


if __name__ == "__main__":
    m = main()
    print("calls", m["n_calls"], "connect", round(m["connect_overall"], 4))
    print("weekend", round(m["connect_weekend"], 4), "weekday", round(m["connect_weekday"], 4))
    print("B7xBR wrong", round(m["b7br_wrong_rate"], 4), "rest", round(m["rest_wrong_rate"], 4))
    print("memo ->", ROOT / "MEMO.md")
