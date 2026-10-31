from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    disposition TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn


def insert_call(conn: sqlite3.Connection, account_id: str, disposition: str, attempt: int, created_at: str) -> None:
    conn.execute(
        "INSERT INTO calls (account_id, disposition, attempt, created_at) VALUES (?, ?, ?, ?)",
        (account_id, disposition, attempt, created_at),
    )
    conn.commit()
