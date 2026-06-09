"""Helpers for calling async code from synchronous agent pipelines."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


def run_sync_async(coro: Coroutine[object, object, T]) -> T:
    """Run a coroutine from sync code (e.g. FastAPI sync routes, pytest)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()
