"""Session Assembly node (Pipeline 3, step 1).

Reads all session_events from Butterbase and folds them into the structured session
JSON that Cognee ingests and the report node summarizes (plan §5 Pipeline 3).
"""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase


def build(bb: Butterbase, *, child_id: str, session_id: str) -> dict[str, Any]:
    events = bb.select("session_events", session_id=session_id)
    session_row = bb.select("sessions", id=session_id)
    sandbox_id = session_row[0]["sandbox_id"] if session_row else None

    completed = [e for e in events if e["event_type"] == "level_complete"]
    failed = [e for e in events if e["event_type"] == "level_fail"]
    replans = [e for e in events if e["event_type"] == "replan_triggered"]
    videos = [e for e in events if e["event_type"] == "video_watched"]

    return {
        "child_id": child_id,
        "session_id": session_id,
        "sandbox_id": sandbox_id,
        "total_minutes": _total_minutes(events),
        "levels_completed": [e["level_index"] for e in completed],
        "levels_failed": [e["level_index"] for e in failed],
        "replan_events": replans,
        "videos_watched": videos,
        "attention_arc": _attention_arc(events),
        "completion_rate": _completion_rate(completed, events),
        "medication_logged": _medication(bb, child_id),
    }


def _total_minutes(events: list[dict[str, Any]]) -> float:
    times = [e["payload"].get("time_on_level_seconds", 0) for e in events]
    return round(sum(times) / 60.0, 1)


def _attention_arc(events: list[dict[str, Any]]) -> list[dict[str, int]]:
    """Errors bucketed by 5-minute window over the session timeline."""
    # TODO(Person B): bucket level_fail events by elapsed minute.
    return []


def _completion_rate(completed: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    starts = {e["level_index"] for e in events if e["event_type"] == "level_start"}
    return round(len(completed) / len(starts), 2) if starts else 0.0


def _medication(bb: Butterbase, child_id: str) -> dict[str, Any] | None:
    logs = bb.select("medication_logs", child_id=child_id)
    return logs[-1] if logs else None
