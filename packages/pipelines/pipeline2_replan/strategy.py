"""Replan-strategy LLM node (Pipeline 2, step 2).

Decides how to restructure around a struggle given the prerequisite path and the
remaining attention window (plan §5, §6 Feature 2).
"""

from __future__ import annotations

from typing import Any

# Below this many seconds, skip the video and go straight to the replanned level.
_MIN_VIDEO_ATTENTION_SECONDS = 120


def decide(
    *,
    prerequisite_path: list[str],
    remaining_attention_seconds: int,
    concept_tag: str,
    level_index: int,
) -> dict[str, Any]:
    """Return the replan plan consumed by the Daytona rewrite + output nodes.

    Deterministic rule scaffold (plan §5); swap for an AI-gateway call
    (task=replan_strategy) that authors `replacement_level_code`.
    """
    steps_away = max(0, len(prerequisite_path) - 1)

    if remaining_attention_seconds < _MIN_VIDEO_ATTENTION_SECONDS:
        strategy = "confidence_builder"  # save the hard concept for next session
        include_video = False
    elif steps_away <= 1:
        strategy = "prerequisite_inject"  # inject one simpler micro-level first
        include_video = True
    else:
        strategy = "reorder"  # address foundations before re-attempting
        include_video = True

    return {
        "strategy": strategy,
        "include_video": include_video,
        "explanation": _explain(strategy, concept_tag),
        "prerequisite_path": prerequisite_path,
        # TODO(Person B): AI gateway authors the actual level code for the strategy.
        "replacement_level_code": _placeholder_level_code(level_index, strategy),
    }


def _explain(strategy: str, concept: str) -> str:
    return {
        "prerequisite_inject": f"Adding a simpler {concept} step first.",
        "reorder": f"Covering the building blocks for {concept} before trying again.",
        "confidence_builder": "Switching to an easier win — we'll revisit this next time.",
    }[strategy]


def _placeholder_level_code(level_index: int, strategy: str) -> str:
    return f'# level_{level_index}.py — regenerated for strategy={strategy}\n'
