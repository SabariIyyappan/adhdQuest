"""Cognee custom nodes — recall (Pipeline 1) and ingest (Pipeline 3).

These wrap the backend Cognee client (packages/backend/cognee) so the pipeline
canvas gets simple, synchronous-looking node functions. Kept thin: all memory logic
lives in the backend wrappers, which own the Neo4j-backed dataset conventions.
"""

from __future__ import annotations

import asyncio
from typing import Any

# The backend package is importable in the pipeline env (installed as a path dep).
from backend.cognee import client as cognee_client


def recall(child_id: str) -> dict[str, Any]:
    """Pipeline 1 step 4 — prior behavioral context for the game-spec node.
    Returns a well-formed empty context on a cold start (first session)."""
    return asyncio.run(cognee_client.recall(child_id))


def ingest(session_json: dict[str, Any], child_id: str) -> None:
    """Pipeline 3 step 2 — remember -> cognify -> memify, in order."""

    async def _run() -> None:
        await cognee_client.remember(session_json, child_id)
        await cognee_client.cognify(child_id)
        await cognee_client.memify(child_id)

    asyncio.run(_run())
