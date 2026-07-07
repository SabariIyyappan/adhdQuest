"""Game-spec generation — the two LLM nodes of Pipeline 1.

`score_assignment` (fast model) computes assignment metadata; `generate`
(strong model) produces the personalized game spec. Personalization rules
(plan §6 Feature 1) are encoded in the prompt and post-processed here so ordering
is deterministic and testable.
"""

from __future__ import annotations

from typing import Any

from ..nodes.ner_node import TaggedQuestion

# No more than 2 consecutive levels share a mechanic (plan §6 Feature 1).
_MAX_CONSECUTIVE_MECHANIC = 2

# Mechanic assignment by operation type.
_MECHANIC_BY_TOPIC = {
    "division": "maze",
    "fractions": "matching",
    "word_problem": "quest",
    "addition": "speed_round",
    "subtraction": "speed_round",
    "multiplication": "puzzle",
    "decimals": "puzzle",
}


def score_assignment(questions: list[TaggedQuestion]) -> dict[str, Any]:
    """Fast-model node: total count, avg difficulty, load category, session splits."""
    # TODO(Person B): call AI gateway (task=assignment_metadata). Deterministic stub:
    total = len(questions)
    avg = sum(q.difficulty for q in questions) / total if total else 0.0
    load = "light" if avg < 2 else "moderate" if avg < 3.5 else "heavy"
    return {
        "total_questions": total,
        "avg_difficulty": avg,
        "estimated_attention_load": load,
    }


def generate(
    *,
    questions: list[TaggedQuestion],
    metadata: dict[str, Any],
    prior_context: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Strong-model node: produce the game spec (validated by game_spec.schema.json)."""
    # TODO(Person B): call AI gateway (task=game_spec) with curriculum RAG + prior_context.
    # The stub below encodes the deterministic ordering rules so downstream nodes work.
    ordered = _order_levels(questions, prior_context)
    levels = [
        {
            "level_index": i,
            "question_id": q.question_id,
            "question_text": q.text,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "mechanic": _MECHANIC_BY_TOPIC.get(q.topic, "puzzle"),
            "is_attention_checkpoint": False,
        }
        for i, q in enumerate(ordered)
    ]
    _insert_attention_checkpoints(levels, profile.get("attention_baseline_minutes", 15))
    return {
        "session_id": None,  # filled by output node after the sessions row is created
        "estimated_session_minutes": _estimate_minutes(metadata),
        "levels": levels,
        "replan": {"fail_threshold": 3},
        "attention": {
            "checkpoint_interval_levels": max(1, profile.get("attention_baseline_minutes", 15) // 3),
            "baseline_minutes": profile.get("attention_baseline_minutes", 15),
        },
    }


def _order_levels(
    questions: list[TaggedQuestion], prior_context: dict[str, Any]
) -> list[TaggedQuestion]:
    """Easy->hard by default; front-load struggle topics if Cognee remembers them."""
    ordered = sorted(questions, key=lambda q: q.difficulty)
    struggle = set(prior_context.get("struggle_topics") or [])
    if struggle:
        # place struggle-topic questions before fatigue (plan §6 Feature 1)
        ordered.sort(key=lambda q: (q.topic not in struggle, q.difficulty))
    return ordered


def _insert_attention_checkpoints(levels: list[dict[str, Any]], baseline_minutes: int) -> None:
    interval = max(1, baseline_minutes // 3)
    for i, level in enumerate(levels):
        if i > 0 and i % interval == 0:
            level["is_attention_checkpoint"] = True


def _estimate_minutes(metadata: dict[str, Any]) -> int:
    return int(metadata["total_questions"] * 1.5)
