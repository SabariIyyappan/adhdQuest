"""Pipeline 3 — Session Memory & Report (plan §5).

Trigger: realtime session_end event.
Sequence: assemble session JSON -> Cognee ingest (remember/cognify/memify) ->
Neo4j GDS analysis -> report-synthesis LLM -> Butterbase output (report + stop sandbox).
"""

from __future__ import annotations

from typing import Any

from ..common import providers
from ..nodes import cognee_nodes, daytona_node, neo4j_gds_node
from . import assemble, report


def run(request: dict[str, Any]) -> dict[str, Any]:
    """request = {child_id, session_id}"""
    _bb = providers.get_butterbase()
    child_id = request["child_id"]
    session_id = request["session_id"]

    # 1. Assemble structured session JSON from session_events.
    session_json = assemble.build(_bb, child_id=child_id, session_id=session_id)

    # 2. Cognee ingest — remember -> cognify -> memify (writes into Neo4j).
    cognee_nodes.ingest(session_json, child_id)

    # 3. Neo4j GDS analysis — bottleneck, struggle patterns, attention trend.
    analysis = {
        "bottleneck": neo4j_gds_node.bottleneck_concept(child_id),
        "struggle_patterns": neo4j_gds_node.struggle_patterns(child_id),
        "attention_trend": neo4j_gds_node.attention_trend(child_id),
    }

    # 4. Report synthesis (strong model) -> Contract E report JSON.
    report_json = report.synthesize(session_json=session_json, analysis=analysis, child_id=child_id)

    # 5. Output — persist report, mark session complete, stop the sandbox.
    from . import output

    return output.publish(
        bb=_bb,
        child_id=child_id,
        session_id=session_id,
        report_json=report_json,
        sandbox_id=session_json.get("sandbox_id"),
    )
