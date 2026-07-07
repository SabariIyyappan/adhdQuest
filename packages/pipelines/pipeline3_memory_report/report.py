"""Report-synthesis LLM node (Pipeline 3, step 4).

Combines this session's stats, the GDS analysis, and Cognee's full-history recall
into the Contract E report JSON — a parent summary + a full doctor narrative. The
deterministic structure is assembled here; the two narratives (and the medication
"observed_effect") come from the AI gateway (``task=report_narrative``), which falls
back to a deterministic local generator offline.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..common import ai_gateway, providers

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
    """Produce the Contract E report."""
    cognee_client = providers.get_cognee()
    history = asyncio.run(cognee_client.graph_qa(child_id, "overall progress summary"))

    bottleneck = analysis["bottleneck"][0] if analysis["bottleneck"] else {"concept": "", "score": 0}
    bottleneck_concept = bottleneck.get("concept", "")

    completed = session_json["levels_completed"]
    total_levels = len(set(completed) | set(session_json["levels_failed"])) or len(completed)

    concept_performance = session_json.get("concept_performance", [])
    start_with = _best_concept(concept_performance)

    session_summary = {
        "total_minutes": session_json["total_minutes"],
        "levels_completed": len(completed),
        "levels_total": total_levels,
        "completion_rate": session_json["completion_rate"],
        "replan_count": len(session_json["replan_events"]),
        "videos_watched": len(session_json["videos_watched"]),
    }

    # Strong-model narratives (deterministic offline).
    narrative = ai_gateway.generate(
        "report_narrative",
        system=REPORT_SYSTEM_PROMPT,
        context={
            "session_summary": session_summary,
            "concept_performance": concept_performance,
            "bottleneck_concept": bottleneck_concept,
            "attention_trend": analysis.get("attention_trend", []),
            "history": history,
            "start_with_concept": start_with,
            "medication_logged": session_json.get("medication_logged"),
        },
    )

    return {
        "session_summary": session_summary,
        "attention_arc": session_json["attention_arc"],
        "concept_performance": concept_performance,
        "bottleneck_concept": bottleneck_concept,
        "bottleneck_centrality_score": bottleneck.get("score", 0.0),
        "parent_summary": narrative.get("parent_summary", ""),
        "doctor_narrative": narrative.get("doctor_narrative", ""),
        "next_session_recommendations": {
            "suggested_duration_minutes": max(12, int(session_json["total_minutes"] * 0.8)),
            "prioritize_concepts": [bottleneck_concept] if bottleneck_concept else [],
            "start_with_concept": narrative.get("start_with_concept", start_with),
        },
        "medication_correlation": _medication_correlation(session_json, narrative),
    }


def _best_concept(concept_performance: list[dict[str, Any]]) -> str:
    """Open the next session with the child's strongest concept (confidence boost)."""
    if not concept_performance:
        return ""
    best = min(concept_performance, key=lambda c: c.get("fail_rate", 1.0))
    return best.get("concept", "")


def _medication_correlation(
    session_json: dict[str, Any], narrative: dict[str, Any]
) -> dict[str, Any] | None:
    med = session_json.get("medication_logged")
    if not med:
        return None
    return {
        "time_delta_minutes": med.get("time_delta_minutes", 0),
        "medication": med.get("medication_name", med.get("medication", "")),
        "observed_effect": narrative.get("medication_effect", ""),
    }
