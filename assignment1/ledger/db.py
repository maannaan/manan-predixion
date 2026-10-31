from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    emi_amount_paise INTEGER NOT NULL CHECK (emi_amount_paise >= 0),
    outstanding_paise INTEGER NOT NULL CHECK (outstanding_paise >= 0),
    due_date TEXT NOT NULL CHECK (length(due_date) = 10)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id TEXT NOT NULL REFERENCES loans(loan_id),
    amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
    applied_paise INTEGER NOT NULL CHECK (applied_paise >= 0),
    excess_paise INTEGER NOT NULL CHECK (excess_paise >= 0),
    paid_at TEXT NOT NULL,
    gateway_txn_id TEXT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_payments_loan_id ON payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_payments_paid_at ON payments(paid_at);
CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(path: str | Path) -> sqlite3.Connection:
    """Create loans and payments tables with constraints. Returns a connection."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    conn.executescript(SCHEMA)
    return conn
