"""Pipeline 1 output node — persist session + push realtime game_ready event."""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase
from ..nodes.daytona_node import BuildResult

_ACTIVE_SESSION_TTL = 2 * 60 * 60  # 2h, matches config/kv_keys.ts


def publish(
    *,
    bb: Butterbase,
    child_id: str,
    assignment_id: str,
    spec: dict[str, Any],
    build: BuildResult,
) -> dict[str, Any]:
    # Create the session row (status active) with the game URL.
    session = bb.insert(
        "sessions",
        {
            "child_id": child_id,
            "assignment_id": assignment_id,
            "sandbox_id": build.sandbox_id,
            "game_url": build.game_url,
            "status": "active",
        },
    )
    session_id = session["id"]

    # Seed live session state in KV for the durable actor.
    bb.kv_set(
        f"session:{child_id}:active",
        {
            "sandbox_id": build.sandbox_id,
            "current_level": 0,
            "fail_count_by_level": {},
            "replan_count": 0,
            "session_start_epoch": 0,
            "attention_seconds_elapsed": 0,
        },
        ttl_seconds=_ACTIVE_SESSION_TTL,
    )

    # Realtime push — Contract C game_ready.
    bb.publish(
        f"child:{child_id}:session",
        {"event": "game_ready", "game_url": build.game_url, "level_count": len(spec["levels"])},
    )

    # Contract B — returned to RocketRide output + persisted.
    return {
        "session_id": session_id,
        "game_url": build.game_url,
        "sandbox_id": build.sandbox_id,
        "level_map": [
            {
                "level_index": lvl["level_index"],
                "question_id": lvl["question_id"],
                "topic": lvl["topic"],
                "difficulty": lvl["difficulty"],
            }
            for lvl in spec["levels"]
        ],
        "estimated_session_minutes": spec["estimated_session_minutes"],
    }
