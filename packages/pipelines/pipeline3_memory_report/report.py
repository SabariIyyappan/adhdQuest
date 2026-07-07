"""Report-synthesis LLM node (Pipeline 3, step 4).

Combines this session's stats, the GDS analysis, and Cognee's full-history recall
into the Contract E report JSON — a parent summary + a full doctor narrative.
"""

from __future__ import annotations

from typing import Any

from backend.cognee import client as cognee_client

REPORT_SYSTEM_PROMPT = """\
You are the ADHDQuest clinical report writer. Given one session's stats, graph
analytics (bottleneck concept, struggle patterns, attention trend), and the child's
full memory, produce:
  - parent_summary: 3 warm, plain-English sentences,
  - doctor_narrative: clinical detail incl. concept bottleneck ranking, attention
    trend, and medication correlation if logged,
  - next_session_recommendations: duration, concepts to prioritize, concept to open with.
Return only JSON matching Contract E (report.ts / SessionReport).
"""


def synthesize(
    *, session_json: dict[str, Any], analysis: dict[str, Any], child_id: str
) -> dict[str, Any]:
    """Produce the Contract E report. Scaffold assembles the deterministic parts;
    swap the narratives for an AI-gateway call (task=report_synthesis)."""
    import asyncio

    history = asyncio.run(cognee_client.graph_qa(child_id, "overall progress summary"))
    bottleneck = analysis["bottleneck"][0] if analysis["bottleneck"] else {"concept": "", "score": 0}

    completed = session_json["levels_completed"]
    total_levels = len(set(completed) | set(session_json["levels_failed"])) or len(completed)

    return {
        "session_summary": {
            "total_minutes": session_json["total_minutes"],
            "levels_completed": len(completed),
            "levels_total": total_levels,
            "completion_rate": session_json["completion_rate"],
            "replan_count": len(session_json["replan_events"]),
            "videos_watched": len(session_json["videos_watched"]),
        },
        "attention_arc": session_json["attention_arc"],
        "concept_performance": [],  # TODO(Person B): derive per-concept fail rates
        "bottleneck_concept": bottleneck.get("concept", ""),
        "bottleneck_centrality_score": bottleneck.get("score", 0.0),
        "parent_summary": "",  # filled by report_synthesis LLM call
        "doctor_narrative": "",  # filled by report_synthesis LLM call
        "next_session_recommendations": {
            "suggested_duration_minutes": max(12, int(session_json["total_minutes"] * 0.8)),
            "prioritize_concepts": [bottleneck.get("concept", "")] if bottleneck.get("concept") else [],
            "start_with_concept": "",
        },
        "medication_correlation": _medication_correlation(session_json, history),
    }


def _medication_correlation(session_json: dict[str, Any], history: Any) -> dict[str, Any] | None:
    med = session_json.get("medication_logged")
    if not med:
        return None
    # TODO(Person B): let report_synthesis LLM cite the correlation from `history`.
    return {
        "time_delta_minutes": med.get("time_delta_minutes", 0),
        "medication": med.get("medication_name", ""),
        "observed_effect": "",
    }
