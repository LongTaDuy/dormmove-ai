"""Pytest configuration shared by the test suite.

Point the application's SQLite session store at a throwaway temp database before
any app module is imported, so tests never touch the real ``local_data``
database. This runs at collection time, before the test modules (which import
``app.main``) are loaded.
"""

from __future__ import annotations

import os
import tempfile

# Unique per test run; the OS cleans up its temp directory.
_TMP_DIR = tempfile.mkdtemp(prefix="dormmove_test_")
os.environ["DORMMOVE_SQLITE_PATH"] = os.path.join(_TMP_DIR, "test_sessions.sqlite3")
