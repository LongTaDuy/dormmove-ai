"""SQLite-backed persistent session memory.

``SessionService`` stores chat sessions, messages, and plan snapshots so the
``/chat`` flow survives restarts. It serializes Pydantic models to JSON columns
and reconstructs them on read.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.memory.sqlite_store import SqliteStore
from app.models.schemas import (
    CreateSessionResponse,
    MoveInPlan,
    ScoreBreakdown,
    SessionSnapshotResponse,
    SessionSummary,
    StudentMoveInProfile,
    Verdict,
)

DEFAULT_TITLE = "DormMove Plan"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


class SessionNotFoundError(LookupError):
    """Raised when an operation targets a session that does not exist."""


class SessionService:
    """Persistent session memory backed by SQLite."""

    def __init__(self, db_path: str) -> None:
        self.store = SqliteStore(db_path)

    # -- lifecycle ---------------------------------------------------------

    def initialize(self) -> None:
        self.store.initialize()

    def close(self) -> None:
        self.store.close()

    # -- sessions ----------------------------------------------------------

    def create_session(self, title: str | None = None) -> CreateSessionResponse:
        session_id = _new_id()
        now = _now()
        self.store.execute(
            """
            INSERT INTO sessions
                (session_id, title, created_at, updated_at, profile_json)
            VALUES (?, ?, ?, ?, '{}')
            """,
            (session_id, title or DEFAULT_TITLE, now, now),
        )
        return CreateSessionResponse(session_id=session_id)

    def session_exists(self, session_id: str) -> bool:
        row = self.store.query_one(
            "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
        )
        return row is not None

    def list_sessions(self) -> list[SessionSummary]:
        rows = self.store.query_all(
            "SELECT * FROM sessions ORDER BY updated_at DESC, rowid DESC"
        )
        summaries: list[SessionSummary] = []
        for row in rows:
            profile = self._profile_from_json(row["profile_json"])
            verdict = self._verdict_from_json(row["latest_score_json"])
            count_row = self.store.query_one(
                "SELECT COUNT(*) AS c FROM messages WHERE session_id = ?",
                (row["session_id"],),
            )
            message_count = count_row["c"] if count_row else 0
            summaries.append(
                SessionSummary(
                    session_id=row["session_id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    school_name=profile.school_name,
                    dorm_name=profile.dorm_name,
                    move_in_date=profile.move_in_date,
                    verdict=verdict,
                    message_count=message_count,
                )
            )
        return summaries

    def get_session_snapshot(self, session_id: str) -> SessionSnapshotResponse:
        row = self._require_session(session_id)
        return SessionSnapshotResponse(
            session_id=session_id,
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            profile=self._profile_from_json(row["profile_json"]),
            messages=self.get_history(session_id),
            latest_plan=self._plan_from_json(row["latest_plan_json"]),
            latest_score=self._score_from_json(row["latest_score_json"]),
        )

    # -- profile -----------------------------------------------------------

    def get_profile(self, session_id: str) -> StudentMoveInProfile:
        row = self.store.query_one(
            "SELECT profile_json FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        if row is None:
            return StudentMoveInProfile()
        return self._profile_from_json(row["profile_json"])

    def save_profile(
        self, session_id: str, profile: StudentMoveInProfile
    ) -> None:
        self._require_session(session_id)
        self.store.execute(
            "UPDATE sessions SET profile_json = ?, updated_at = ? "
            "WHERE session_id = ?",
            (profile.model_dump_json(), _now(), session_id),
        )

    # -- messages ----------------------------------------------------------

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        meta: dict | None = None,
    ) -> None:
        self._require_session(session_id)
        now = _now()
        self.store.execute(
            """
            INSERT INTO messages
                (message_id, session_id, role, content, created_at, meta_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_new_id(), session_id, role, content, now, json.dumps(meta or {})),
        )
        self.store.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (now, session_id),
        )

    def get_history(self, session_id: str) -> list[dict]:
        rows = self.store.query_all(
            "SELECT message_id, role, content, created_at, meta_json "
            "FROM messages WHERE session_id = ? "
            "ORDER BY created_at ASC, rowid ASC",
            (session_id,),
        )
        history: list[dict] = []
        for row in rows:
            history.append(
                {
                    "message_id": row["message_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "created_at": row["created_at"],
                    "meta": json.loads(row["meta_json"] or "{}"),
                }
            )
        return history

    # -- plans -------------------------------------------------------------

    def save_plan_snapshot(
        self, session_id: str, plan: MoveInPlan, score: ScoreBreakdown
    ) -> None:
        self._require_session(session_id)
        now = _now()
        plan_json = plan.model_dump_json()
        score_json = score.model_dump_json()
        self.store.execute(
            """
            INSERT INTO plan_snapshots
                (snapshot_id, session_id, plan_json, score_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_new_id(), session_id, plan_json, score_json, now),
        )
        self.store.execute(
            "UPDATE sessions SET latest_plan_json = ?, latest_score_json = ?, "
            "updated_at = ? WHERE session_id = ?",
            (plan_json, score_json, now, session_id),
        )

    def get_latest_plan(self, session_id: str) -> MoveInPlan | None:
        row = self.store.query_one(
            "SELECT latest_plan_json FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        if row is None:
            return None
        return self._plan_from_json(row["latest_plan_json"])

    # -- helpers -----------------------------------------------------------

    def _require_session(self, session_id: str):
        row = self.store.query_one(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        if row is None:
            raise SessionNotFoundError(session_id)
        return row

    @staticmethod
    def _profile_from_json(raw: str | None) -> StudentMoveInProfile:
        if not raw or raw == "{}":
            return StudentMoveInProfile()
        return StudentMoveInProfile.model_validate_json(raw)

    @staticmethod
    def _plan_from_json(raw: str | None) -> MoveInPlan | None:
        if not raw:
            return None
        return MoveInPlan.model_validate_json(raw)

    @staticmethod
    def _score_from_json(raw: str | None) -> ScoreBreakdown | None:
        if not raw:
            return None
        return ScoreBreakdown.model_validate_json(raw)

    @staticmethod
    def _verdict_from_json(raw: str | None) -> Verdict:
        if not raw:
            return Verdict.NEEDS_WORK
        try:
            data = json.loads(raw)
            return Verdict(data.get("verdict", Verdict.NEEDS_WORK.value))
        except (ValueError, KeyError):
            return Verdict.NEEDS_WORK
