"""Thin, typed wrappers around the Cognee API used by the RocketRide pipelines.

Cognee is configured with a Neo4j graph backend and a LanceDB vector store, so
`cognify()` writes entities/relationships directly into the same Neo4j instance
that holds our hand-authored schema (plan §3, "Cognee's Relationship with Neo4j").

Each child gets an isolated user set named via :func:`dataset_name`, giving per-child
memory isolation and a clean unit for GDPR deletion.
"""

from __future__ import annotations

import json
import re
from typing import Any

import cognee  # provided by the Cognee SDK in the pipeline environment

from .config import configure_cognee

# Asking for a strict JSON object makes GRAPH_COMPLETION output parseable into the
# stable `prior_context` shape the game-spec node consumes.
_RECALL_QUERY = (
    "Summarize this child's learning history as a JSON object with exactly these keys: "
    '"struggle_topics" (array of concept name strings), '
    '"attention_window_minutes" (number or null), '
    '"preferred_explanation_style" (string or null), '
    '"last_session_summary" (string or null), '
    '"medication_correlation" (string or null). '
    "Base every value only on the stored memory. Respond with JSON only, no prose."
)


def dataset_name(child_id: str) -> str:
    """Deterministic per-child user-set / dataset name. Keep in sync with the KV key
    `child:{child_id}:cognee_dataset` set by the backend."""
    return f"child_{child_id}"


async def recall(child_id: str, query: str = _RECALL_QUERY) -> dict[str, Any]:
    """Pipeline 1 — retrieve prior behavioral memory for a child.

    Returns known struggle topics, attention window, preferred explanation style,
    last-session summary, and any medication correlations. Empty on first session.
    """
    configure_cognee()
    results = await cognee.search(
        query_text=query,
        query_type="GRAPH_COMPLETION",
        datasets=[dataset_name(child_id)],
    )
    return _normalize_recall(results)


async def remember(session_json: dict[str, Any], child_id: str) -> None:
    """Pipeline 3 step 1 — ingest raw session data into the child's dataset."""
    configure_cognee()
    await cognee.add(session_json, dataset_name=dataset_name(child_id))


async def cognify(child_id: str) -> None:
    """Pipeline 3 step 2 — run the ECL pipeline (classify -> extract -> embed ->
    commit to Neo4j) over newly-added data for this child."""
    configure_cognee()
    await cognee.cognify(datasets=[dataset_name(child_id)])


async def memify(child_id: str) -> None:
    """Pipeline 3 step 3 — refine the memory graph: strengthen recurring edges,
    prune one-off anomalies, add derived temporal facts."""
    configure_cognee()
    await cognee.memify(datasets=[dataset_name(child_id)])


async def graph_qa(child_id: str, question: str) -> dict[str, Any]:
    """Doctor dashboard Q&A — cited GRAPH_COMPLETION answer over the child's memory."""
    configure_cognee()
    return await cognee.search(
        query_text=question,
        query_type="GRAPH_COMPLETION",
        datasets=[dataset_name(child_id)],
    )


async def forget(child_id: str) -> None:
    """GDPR — wipe all memory for a child (account/child deletion)."""
    configure_cognee()
    await cognee.prune.prune_data(dataset=dataset_name(child_id))


# --- recall normalization -------------------------------------------------

_EMPTY_CONTEXT: dict[str, Any] = {
    "struggle_topics": [],
    "attention_window_minutes": None,
    "preferred_explanation_style": None,
    "last_session_summary": None,
    "medication_correlation": None,
}


def _normalize_recall(raw: Any) -> dict[str, Any]:
    """Coerce Cognee's search output into the stable `prior_context` shape the
    game-spec LLM node expects. Well-formed empty on a cold start; parsed from the
    model's JSON answer otherwise. Always attaches the untouched `raw` for tracing.
    """
    context = dict(_EMPTY_CONTEXT)
    answer = _extract_answer_text(raw)
    parsed = _parse_json_object(answer) if answer else None

    if isinstance(parsed, dict):
        for key in _EMPTY_CONTEXT:
            if parsed.get(key) not in (None, "", []):
                context[key] = parsed[key]
        # Normalize the two most misuse-prone fields.
        context["struggle_topics"] = _as_str_list(context["struggle_topics"])
        context["attention_window_minutes"] = _as_number(context["attention_window_minutes"])
    elif answer:
        # Model returned prose rather than JSON — keep it as the session summary
        # so the game-spec node still gets a usable signal.
        context["last_session_summary"] = answer.strip()

    context["raw"] = raw
    return context


def _extract_answer_text(raw: Any) -> str | None:
    """Pull the natural-language answer out of Cognee's varied return shapes."""
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        for key in ("answer", "result", "text", "content"):
            if isinstance(raw.get(key), str):
                return raw[key]
        return None
    if isinstance(raw, list):
        for item in raw:
            text = _extract_answer_text(item)
            if text:
                return text
    return None


def _parse_json_object(text: str) -> Any:
    """Parse a JSON object out of a completion, tolerating surrounding prose/fences."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v not in (None, "")]
    if isinstance(value, str) and value:
        return [value]
    return []


def _as_number(value: Any) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return None
    return None
