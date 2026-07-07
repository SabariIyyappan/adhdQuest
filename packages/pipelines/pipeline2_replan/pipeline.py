"""Pipeline 2 — Struggle Replan (plan §5).

Trigger: durable actor webhook when fail_count on a level reaches 3.
Sequence: Neo4j GDS prerequisite path -> replan-strategy LLM -> YouTube lookup ->
Daytona live rewrite -> Butterbase output (event + video + realtime push).
"""

from __future__ import annotations

from typing import Any

from ..common import providers
from ..nodes import daytona_node, neo4j_gds_node, youtube_node
from . import strategy


def run(request: dict[str, Any]) -> dict[str, Any]:
    """request = {child_id, session_id, current_level_index, concept_tag,
    time_elapsed_seconds, attention_baseline_seconds}"""
    child_id = request["child_id"]
    session_id = request["session_id"]
    level_index = request["current_level_index"]
    concept = request["concept_tag"]

    remaining = max(0, request["attention_baseline_seconds"] - request["time_elapsed_seconds"])

    # 1. Neo4j GDS — prerequisite path from mastered ancestor to the blocked concept.
    prereq_path = neo4j_gds_node.prerequisite_path(child_id, concept)

    # 2. Replan strategy (strong model).
    plan = strategy.decide(
        prerequisite_path=prereq_path,
        remaining_attention_seconds=remaining,
        concept_tag=concept,
        level_index=level_index,
    )

    # 3. YouTube micro-lesson (None if attention too low or plan skips it).
    video = None
    if plan["include_video"]:
        video = youtube_node.run(
            concept_tag=concept,
            remaining_attention_seconds=remaining,
            grade_level=request.get("grade_level", 5),
        )

    # 4. Daytona — hot-reload the rewritten level in place.
    daytona_node.rewrite_level(
        sandbox_id=_sandbox_id(child_id),
        level_index=level_index,
        level_code=plan["replacement_level_code"],
    )

    # 5. Output — persist + realtime replan push.
    from . import output

    return output.publish(
        bb=providers.get_butterbase(),
        child_id=child_id,
        session_id=session_id,
        level_index=level_index,
        plan=plan,
        video=video,
    )


def _sandbox_id(child_id: str) -> str:
    state = providers.get_butterbase().kv_get(f"session:{child_id}:active") or {}
    return state["sandbox_id"]
