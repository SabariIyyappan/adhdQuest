"""Thin, typed wrappers around the Cognee API used by the RocketRide pipelines.

Cognee is configured with a Neo4j graph backend and a LanceDB vector store, so
`cognify()` writes entities/relationships directly into the same Neo4j instance
that holds our hand-authored schema (plan §3, "Cognee's Relationship with Neo4j").

Each child gets an isolated user set named via :func:`dataset_name`, giving per-child
memory isolation and a clean unit for GDPR deletion.
"""

from __future__ import annotations

from typing import Any

import cognee  # provided by the Cognee SDK in the pipeline environment


def dataset_name(child_id: str) -> str:
    """Deterministic per-child user-set / dataset name. Keep in sync with the KV key
    `child:{child_id}:cognee_dataset` set by the backend."""
    return f"child_{child_id}"


async def recall(child_id: str, query: str = "learning patterns and attention history") -> dict[str, Any]:
    """Pipeline 1 — retrieve prior behavioral memory for a child.

    Returns known struggle topics, attention window, preferred explanation style,
    last-session summary, and any medication correlations. Empty on first session.
    """
    results = await cognee.search(
        query_text=query,
        query_type="GRAPH_COMPLETION",
        datasets=[dataset_name(child_id)],
    )
    return _normalize_recall(results)


async def remember(session_json: dict[str, Any], child_id: str) -> None:
    """Pipeline 3 step 1 — ingest raw session data into the child's dataset."""
    await cognee.add(session_json, dataset_name=dataset_name(child_id))


async def cognify(child_id: str) -> None:
    """Pipeline 3 step 2 — run the ECL pipeline (classify -> extract -> embed ->
    commit to Neo4j) over newly-added data for this child."""
    await cognee.cognify(datasets=[dataset_name(child_id)])


async def memify(child_id: str) -> None:
    """Pipeline 3 step 3 — refine the memory graph: strengthen recurring edges,
    prune one-off anomalies, add derived temporal facts."""
    await cognee.memify(datasets=[dataset_name(child_id)])


async def graph_qa(child_id: str, question: str) -> dict[str, Any]:
    """Doctor dashboard Q&A — cited GRAPH_COMPLETION answer over the child's memory."""
    return await cognee.search(
        query_text=question,
        query_type="GRAPH_COMPLETION",
        datasets=[dataset_name(child_id)],
    )


async def forget(child_id: str) -> None:
    """GDPR — wipe all memory for a child (account/child deletion)."""
    await cognee.prune.prune_data(dataset=dataset_name(child_id))


def _normalize_recall(raw: Any) -> dict[str, Any]:
    """Coerce Cognee's search output into the stable `prior_context` shape the
    game-spec LLM node expects. Empty-but-well-formed on a cold start."""
    return {
        "struggle_topics": [],
        "attention_window_minutes": None,
        "preferred_explanation_style": None,
        "last_session_summary": None,
        "medication_correlation": None,
        "raw": raw,
    }
