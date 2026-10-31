from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

from ledger.exceptions import InvalidAmountError
from ledger.money import to_paise

REQUIRED_COLUMNS = ("loan_id", "emi_amount", "outstanding_amount", "due_date")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_loans_csv(conn: sqlite3.Connection, path: str | Path) -> list[dict]:
    """Insert loans from CSV. Returns rejected rows: {line, reason}.

    Expected header: loan_id,emi_amount,outstanding_amount,due_date
    Amounts are rupees (2 decimal places). due_date is YYYY-MM-DD.
    """
    rejected: list[dict] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV is empty or missing a header row")
        fields = [name.strip() for name in reader.fieldnames]
        missing = [col for col in REQUIRED_COLUMNS if col not in fields]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        conn.execute("BEGIN IMMEDIATE")
        try:
            for line_no, raw in enumerate(reader, start=2):
                row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
                reason = _validate_row(conn, row)
                if reason:
                    rejected.append({"line": line_no, "reason": reason})
                    continue
                conn.execute(
                    """
                    INSERT INTO loans (loan_id, emi_amount_paise, outstanding_paise, due_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["loan_id"],
                        to_paise(row["emi_amount"]),
                        to_paise(row["outstanding_amount"]),
                        row["due_date"],
                    ),
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return rejected


def _validate_row(conn: sqlite3.Connection, row: dict) -> str | None:
    loan_id = row.get("loan_id") or ""
    if not loan_id:
        return "missing loan_id"
    if conn.execute("SELECT 1 FROM loans WHERE loan_id = ?", (loan_id,)).fetchone():
        return f"duplicate loan_id: {loan_id}"
    due = row.get("due_date") or ""
    if not _DATE_RE.match(due):
        return "due_date must be YYYY-MM-DD"
    try:
        emi = to_paise(row.get("emi_amount") or "")
    except (InvalidAmountError, TypeError):
        return "invalid emi_amount"
    if emi < 0:
        return "emi_amount cannot be negative"
    try:
        outstanding = to_paise(row.get("outstanding_amount") or "")
    except (InvalidAmountError, TypeError):
        return "invalid outstanding_amount"
    if outstanding < 0:
        return "outstanding_amount cannot be negative"
    return None
