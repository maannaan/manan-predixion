from __future__ import annotations

import threading
from decimal import Decimal
from pathlib import Path

import pytest

from ledger import (
    DUPLICATE,
    OVERPAID,
    POSTED,
    InvalidAmountError,
    UnknownLoanError,
    collection_efficiency,
    init_db,
    load_loans_csv,
    post_payment,
)
from ledger.db import connect
from ledger.exceptions import InvalidPaymentError


def _seed_loan(conn, loan_id="L1", emi="1000.00", outstanding="5000.00", due="2026-10-15"):
    from ledger.money import to_paise

    conn.execute(
        """
        INSERT INTO loans (loan_id, emi_amount_paise, outstanding_paise, due_date)
        VALUES (?, ?, ?, ?)
        """,
        (loan_id, to_paise(emi), to_paise(outstanding), due),
    )


def test_happy_path_posts_and_reduces_outstanding(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn)
    status = post_payment(conn, "L1", Decimal("1500.00"), "txn-1")
    assert status == POSTED
    outstanding = conn.execute(
        "SELECT outstanding_paise FROM loans WHERE loan_id = 'L1'"
    ).fetchone()[0]
    assert outstanding == 350000
    payment = conn.execute("SELECT amount_paise, applied_paise, excess_paise FROM payments").fetchone()
    assert tuple(payment) == (150000, 150000, 0)


def test_duplicate_transaction_id_is_idempotent(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn)
    assert post_payment(conn, "L1", "100.00", "txn-dup") == POSTED
    assert post_payment(conn, "L1", "100.00", "txn-dup") == DUPLICATE
    assert post_payment(conn, "L1", "999.00", "txn-dup") == DUPLICATE
    outstanding = conn.execute("SELECT outstanding_paise FROM loans WHERE loan_id = 'L1'").fetchone()[0]
    assert outstanding == 490000
    count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    assert count == 1


def test_exact_payoff_is_posted_not_overpaid(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn, outstanding="100.00")
    assert post_payment(conn, "L1", "100.00", "txn-exact") == POSTED
    assert conn.execute("SELECT outstanding_paise FROM loans").fetchone()[0] == 0
    assert conn.execute("SELECT excess_paise FROM payments").fetchone()[0] == 0


def test_overpayment_zeroes_outstanding_and_records_excess(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn, outstanding="100.00")
    status = post_payment(conn, "L1", Decimal("130.00"), "txn-over")
    assert status == OVERPAID
    loan = conn.execute("SELECT outstanding_paise FROM loans WHERE loan_id = 'L1'").fetchone()
    assert loan[0] == 0
    payment = conn.execute(
        "SELECT amount_paise, applied_paise, excess_paise FROM payments WHERE gateway_txn_id = 'txn-over'"
    ).fetchone()
    assert tuple(payment) == (13000, 10000, 3000)


def test_invalid_amount_rejected(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn)
    with pytest.raises(InvalidAmountError):
        post_payment(conn, "L1", "0", "txn-zero")
    with pytest.raises(InvalidAmountError):
        post_payment(conn, "L1", Decimal("-10.00"), "txn-neg")
    with pytest.raises(InvalidAmountError):
        post_payment(conn, "L1", 1.5, "txn-float")
    with pytest.raises(InvalidPaymentError):
        post_payment(conn, "L1", "10.00", "  ")
    assert conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 0
    assert conn.execute("SELECT outstanding_paise FROM loans").fetchone()[0] == 500000


def test_unknown_loan_rejected(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    with pytest.raises(UnknownLoanError):
        post_payment(conn, "missing", "10.00", "txn-x")
    assert conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 0


def test_eight_threads_same_transaction_exactly_one_succeeds(tmp_path: Path):
    db_path = tmp_path / "ledger.db"
    setup = init_db(db_path)
    _seed_loan(setup, outstanding="1000.00")
    setup.close()

    results: list[str] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(8)

    def worker() -> None:
        conn = connect(db_path)
        try:
            barrier.wait(timeout=10)
            results.append(post_payment(conn, "L1", "250.00", "txn-race"))
        except BaseException as exc:  # noqa: BLE001 — collect any failure for the assertion
            errors.append(exc)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == []
    assert results.count(POSTED) == 1
    assert results.count(DUPLICATE) == 7
    assert len(results) == 8

    conn = connect(db_path)
    outstanding = conn.execute("SELECT outstanding_paise FROM loans WHERE loan_id = 'L1'").fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    assert outstanding == 75000
    assert count == 1
    conn.close()


def test_collection_efficiency(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    _seed_loan(conn, loan_id="L1", emi="1000.00", outstanding="5000.00", due="2026-10-15")
    _seed_loan(conn, loan_id="L2", emi="500.00", outstanding="500.00", due="2026-11-01")
    post_payment(conn, "L1", "300.00", "oct-1")
    post_payment(conn, "L1", "200.00", "oct-2")
    conn.execute("UPDATE payments SET paid_at = '2026-10-05T10:00:00Z'")
    assert collection_efficiency(conn, 2026, 10) == pytest.approx(50000 / 100000)
    assert collection_efficiency(conn, 2026, 11) == pytest.approx(0.0)
    assert collection_efficiency(conn, 2026, 1) == 0.0


def test_load_loans_csv_reports_rejections(tmp_path: Path):
    conn = init_db(tmp_path / "ledger.db")
    csv_path = tmp_path / "loans.csv"
    csv_path.write_text(
        "loan_id,emi_amount,outstanding_amount,due_date\n"
        "A1,1000.00,4000.00,2026-10-01\n"
        ",100.00,100.00,2026-10-01\n"
        "A2,bad,100.00,2026-10-01\n"
        "A3,100.00,100.00,31-10-2026\n"
        "A1,100.00,100.00,2026-10-02\n"
        "A4,250.50,250.50,2026-11-15\n",
        encoding="utf-8",
    )
    rejected = load_loans_csv(conn, csv_path)
    reasons = {item["line"]: item["reason"] for item in rejected}
    assert reasons[3] == "missing loan_id"
    assert reasons[4] == "invalid emi_amount"
    assert reasons[5] == "due_date must be YYYY-MM-DD"
    assert "duplicate loan_id" in reasons[6]
    ids = {row[0] for row in conn.execute("SELECT loan_id FROM loans")}
    assert ids == {"A1", "A4"}
    assert len(rejected) == 4
