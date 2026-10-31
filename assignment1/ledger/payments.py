from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ledger.exceptions import InvalidAmountError, InvalidPaymentError, UnknownLoanError
from ledger.money import AmountInput, to_paise

POSTED = "POSTED"
DUPLICATE = "DUPLICATE"
OVERPAID = "OVERPAID"


def post_payment(
    conn: sqlite3.Connection,
    loan_id: str,
    amount: AmountInput,
    gateway_txn_id: str,
) -> str:
    """Atomically and idempotently post a payment.

    Returns POSTED, DUPLICATE, or OVERPAID.
    Overpayment records the full amount, applies up to outstanding, sets outstanding to 0.
    """
    if not loan_id or not str(loan_id).strip():
        raise UnknownLoanError("loan_id is required")
    if gateway_txn_id is None or not str(gateway_txn_id).strip():
        raise InvalidPaymentError("gateway_txn_id is required")

    amount_paise = to_paise(amount)
    if amount_paise <= 0:
        raise InvalidAmountError("amount must be greater than zero")

    txn_id = str(gateway_txn_id).strip()
    paid_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn.execute("BEGIN IMMEDIATE")
    try:
        try:
            conn.execute(
                """
                INSERT INTO payments (
                    loan_id, amount_paise, applied_paise, excess_paise, paid_at, gateway_txn_id
                ) VALUES (?, ?, 0, 0, ?, ?)
                """,
                (str(loan_id), amount_paise, paid_at, txn_id),
            )
        except sqlite3.IntegrityError as exc:
            conn.execute("ROLLBACK")
            if "UNIQUE" in str(exc).upper() or "gateway_txn_id" in str(exc):
                return DUPLICATE
            # FK failure means unknown loan
            if "FOREIGN KEY" in str(exc).upper():
                raise UnknownLoanError(f"unknown loan_id: {loan_id}") from exc
            raise

        row = conn.execute(
            "SELECT outstanding_paise FROM loans WHERE loan_id = ?",
            (str(loan_id),),
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            raise UnknownLoanError(f"unknown loan_id: {loan_id}")

        outstanding = int(row["outstanding_paise"])
        applied = min(amount_paise, outstanding)
        excess = amount_paise - applied
        new_outstanding = outstanding - applied

        conn.execute(
            """
            UPDATE payments
            SET applied_paise = ?, excess_paise = ?
            WHERE gateway_txn_id = ?
            """,
            (applied, excess, txn_id),
        )
        conn.execute(
            "UPDATE loans SET outstanding_paise = ? WHERE loan_id = ?",
            (new_outstanding, str(loan_id)),
        )
        conn.execute("COMMIT")
        return OVERPAID if excess > 0 else POSTED
    except sqlite3.IntegrityError as exc:
        conn.execute("ROLLBACK")
        if "UNIQUE" in str(exc).upper() or "gateway_txn_id" in str(exc):
            return DUPLICATE
        raise
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
