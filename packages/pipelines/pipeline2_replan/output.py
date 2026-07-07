"""Pipeline 2 output node — persist replan event + video, push realtime replan."""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase


def publish(
    *,
    bb: Butterbase,
    child_id: str,
    session_id: str,
    level_index: int,
    plan: dict[str, Any],
    video: dict[str, Any] | None,
) -> dict[str, Any]:
    # Log the replan as a session event.
    bb.insert(
        "session_events",
        {
            "session_id": session_id,
            "event_type": "replan_triggered",
            "level_index": level_index,
            "payload": {"strategy": plan["strategy"], "explanation": plan["explanation"]},
        },
    )

    # Persist the video recommendation, if any.
    if video:
        bb.insert(
            "video_recommendations",
            {
                "session_id": session_id,
                "level_index": level_index,
                "youtube_id": video["youtube_id"],
                "title": video["title"],
                "duration_seconds": video["duration_seconds"],
                "concept_tag": plan["prerequisite_path"][-1] if plan["prerequisite_path"] else None,
            },
        )

    # Realtime push — Contract C replan.
    bb.publish(
        f"child:{child_id}:session",
        {
            "event": "replan",
            "trigger_level": level_index,
            "strategy": plan["strategy"],
            "explanation": plan["explanation"],
            "video": video,
        },
    )
    return {"replan_applied": True, "strategy": plan["strategy"]}
