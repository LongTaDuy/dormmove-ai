"""Persistent sessions and checkpointing.

Available components:
- SqliteStore: lock-protected SQLite connection wrapper.
- SessionService: SQLite-backed session/message/plan persistence.

Planned components:
- Optional Redis checkpointer for LangGraph state (enabled via REDIS_URL).
"""

from app.memory.session_service import SessionNotFoundError, SessionService
from app.memory.sqlite_store import SqliteStore

__all__ = ["SessionNotFoundError", "SessionService", "SqliteStore"]
