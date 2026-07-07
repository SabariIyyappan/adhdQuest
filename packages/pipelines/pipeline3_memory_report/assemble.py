"""Session Assembly node (Pipeline 3, step 1).

Reads all session_events from Butterbase and folds them into the structured session
JSON that Cognee ingests and the report node summarizes (plan §5 Pipeline 3). All
reads go through the Butterbase client; no sponsor-specific logic leaks in here.
"""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase

_BUCKET_SECONDS = 300  # attention arc is bucketed into 5-minute windows


def build(bb: Butterbase, *, child_id: str, session_id: str) -> dict[str, Any]:
    events = bb.select("session_events", session_id=session_id)
    session_row = bb.select("sessions", id=session_id)
    session = session_row[0] if session_row else {}
    sandbox_id = session.get("sandbox_id")

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
        "concept_performance": _concept_performance(bb, events, session),
        "completion_rate": _completion_rate(completed, events),
        "medication_logged": _medication(bb, child_id),
    }


def _ordered(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chronological order; falls back to input order when timestamps are absent."""
    return sorted(events, key=lambda e: (e.get("timestamp") or "", str(e.get("id") or "")))


def _total_minutes(events: list[dict[str, Any]]) -> float:
    times = [(e.get("payload") or {}).get("time_on_level_seconds", 0) for e in events]
    return round(sum(times) / 60.0, 1)


def _attention_arc(events: list[dict[str, Any]]) -> list[dict[str, int]]:
    """Errors bucketed by 5-minute window over the session timeline.

    Elapsed time is accumulated from each event's ``time_on_level_seconds`` (the game
    emits this on every level event), so we get an errors-over-time arc without
    needing wall-clock timestamps to line up.
    """
    arc: dict[int, int] = {0: 0}
    elapsed = 0
    for e in _ordered(events):
        payload = e.get("payload") or {}
        minute_bucket = (elapsed // _BUCKET_SECONDS) * 5
        arc.setdefault(minute_bucket, 0)
        if e["event_type"] == "level_fail":
            arc[minute_bucket] += 1
        elapsed += payload.get("time_on_level_seconds", 0)
    return [{"minute": m, "errors": arc[m]} for m in sorted(arc)]


def _concept_performance(
    bb: Butterbase, events: list[dict[str, Any]], session: dict[str, Any]
) -> list[dict[str, Any]]:
    """Per-concept avg time + fail rate, joining events to their source question topic."""
    topic_by_level = _topic_by_level(bb, session)
    agg: dict[str, dict[str, Any]] = {}
    for e in events:
        concept = topic_by_level.get(e.get("level_index"))
        if not concept:
            continue
        d = agg.setdefault(concept, {"times": [], "fails": 0, "attempts": 0, "replan": False})
        payload = e.get("payload") or {}
        et = e["event_type"]
        if et == "level_complete":
            d["attempts"] += 1
            if "time_on_level_seconds" in payload:
                d["times"].append(payload["time_on_level_seconds"])
        elif et == "level_fail":
            d["attempts"] += 1
            d["fails"] += 1
        elif et == "replan_triggered":
            d["replan"] = True

    perf: list[dict[str, Any]] = []
    for concept, d in agg.items():
        attempts = d["attempts"] or 1
        perf.append(
            {
                "concept": concept,
                "avg_time_seconds": round(sum(d["times"]) / len(d["times"])) if d["times"] else None,
                "fail_rate": round(d["fails"] / attempts, 2),
                "replan_triggered": d["replan"],
            }
        )
    return perf


def _topic_by_level(bb: Butterbase, session: dict[str, Any]) -> dict[int, str]:
    assignment_id = session.get("assignment_id")
    if not assignment_id:
        return {}
    questions = bb.select("questions", assignment_id=assignment_id)
    return {
        q["level_index"]: (q.get("operation_type") or q.get("topic"))
        for q in questions
        if q.get("level_index") is not None
    }


def _completion_rate(completed: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    starts = {e["level_index"] for e in events if e["event_type"] == "level_start"}
    return round(len(completed) / len(starts), 2) if starts else 0.0


def _medication(bb: Butterbase, child_id: str) -> dict[str, Any] | None:
    logs = bb.select("medication_logs", child_id=child_id)
    return logs[-1] if logs else None
