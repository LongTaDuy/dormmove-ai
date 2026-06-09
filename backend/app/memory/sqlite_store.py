"""Thin SQLite storage layer for session memory.

Wraps a single ``sqlite3`` connection guarded by a lock so it is safe to use
from FastAPI's threadpool (sync routes run in a worker thread). This keeps the
implementation simple and correct; a fully async store (aiosqlite) can replace
it later behind the same method surface.
"""

from __future__ import annotations

import os
import sqlite3
import threading

# DDL is idempotent so initialize() can run on every startup.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id        TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    profile_json      TEXT NOT NULL DEFAULT '{}',
    latest_plan_json  TEXT,
    latest_score_json TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    message_id  TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    meta_json   TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS plan_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    plan_json   TEXT NOT NULL,
    score_json  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_session_created
    ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_session_created
    ON plan_snapshots(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_updated
    ON sessions(updated_at);
"""


class SqliteStore:
    """Lock-protected wrapper around a single SQLite connection."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            # ":memory:" and other special paths have no directory to create.
            parent = os.path.dirname(os.path.abspath(self.db_path))
            if parent and self.db_path != ":memory:":
                os.makedirs(parent, exist_ok=True)
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._conn = conn
        return self._conn

    def initialize(self) -> None:
        with self._lock:
            conn = self._connect()
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(sql, params)
            conn.commit()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            conn = self._connect()
            cur = conn.execute(sql, params)
            return cur.fetchone()

    def query_all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            conn = self._connect()
            cur = conn.execute(sql, params)
            return cur.fetchall()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
