"""SQLite database connection and schema management.

Stores incidents, diagnostic sessions, step execution history, evidence
records, and diagnostic findings with full traceability.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "instance" / "incidents.db"


class DatabaseError(RuntimeError):
    """Raised when a SQLite database operation fails."""


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    device_type TEXT,
    target_os TEXT NOT NULL,
    category TEXT,
    workflow_id TEXT,
    status TEXT NOT NULL,
    safety_warning TEXT,
    resolution_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    session_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    target_os TEXT NOT NULL,
    current_step_id TEXT,
    status TEXT NOT NULL,
    visit_counts_json TEXT NOT NULL,
    ruled_out_json TEXT NOT NULL,
    safety_alert_json TEXT,
    escalation_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS step_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_title TEXT NOT NULL,
    result_code TEXT NOT NULL,
    outcome_id TEXT,
    action_taken TEXT NOT NULL,
    summary TEXT NOT NULL,
    user_notes TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    description TEXT NOT NULL,
    raw_value_json TEXT NOT NULL,
    source TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE
);
"""


class Database:
    """Thin, safe SQLite manager with transactional context management."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection with row dict access and automatic commit/rollback."""
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            if conn is not None:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

    def init_db(self) -> None:
        """Create all required tables if they do not already exist."""
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
