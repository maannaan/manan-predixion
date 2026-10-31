from __future__ import annotations

import sqlite3


def collection_efficiency(conn: sqlite3.Connection, year: int, month: int) -> float:
    """Amount collected in the month divided by EMI due in the month.

    Collected = sum of payment amounts with paid_at in that calendar month (UTC date).
    EMI due = sum of emi_amount for loans whose due_date falls in that month.
    Returns 0.0 if no EMI is due (avoids division by zero).
    """
    if month < 1 or month > 12:
        raise ValueError("month must be in 1..12")
    prefix = f"{int(year):04d}-{int(month):02d}"

    collected_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount_paise), 0) AS collected
        FROM payments
        WHERE substr(paid_at, 1, 7) = ?
        """,
        (prefix,),
    ).fetchone()
    due_row = conn.execute(
        """
        SELECT COALESCE(SUM(emi_amount_paise), 0) AS due
        FROM loans
        WHERE substr(due_date, 1, 7) = ?
        """,
        (prefix,),
    ).fetchone()

    collected = int(collected_row["collected"])
    due = int(due_row["due"])
    if due == 0:
        return 0.0
    return collected / due
