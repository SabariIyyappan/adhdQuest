"""Neo4j GDS custom nodes — prerequisite path (Pipeline 2) + report analytics (Pipeline 3).

Loads named queries from packages/backend/neo4j/queries.cypher so the Cypher stays
owned by Person A and is not duplicated here.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

from ..common.config import settings

_QUERIES_FILE = (
    Path(__file__).resolve().parents[2] / "backend" / "neo4j" / "queries.cypher"
)


@lru_cache(maxsize=1)
def _driver():  # noqa: ANN202 - neo4j Driver
    return GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


@lru_cache(maxsize=1)
def _named_queries() -> dict[str, str]:
    """Parse `// name: xxx` blocks out of the shared queries.cypher file."""
    text = _QUERIES_FILE.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    for match in re.finditer(r"// name: (\w+)\n(.*?)(?=\n// name: |\Z)", text, re.S):
        blocks[match.group(1)] = match.group(2).strip()
    return blocks


def _run(name: str, **params: Any) -> list[dict[str, Any]]:
    query = _named_queries()[name]
    with _driver().session() as session:
        return [record.data() for record in session.run(query, **params)]


def prerequisite_path(child_id: str, blocked_concept: str) -> list[str]:
    """Pipeline 2 — ordered prerequisite concepts from mastered ancestor to blocker."""
    rows = _run("prerequisite_path", child_id=child_id, blocked_concept=blocked_concept)
    return rows[0]["prerequisite_path"] if rows else []


def bottleneck_concept(child_id: str) -> list[dict[str, Any]]:
    """Pipeline 3 — top concepts by betweenness centrality (the bottleneck ranking)."""
    return _run("bottleneck_centrality", child_id=child_id)


def struggle_patterns(child_id: str) -> list[dict[str, Any]]:
    """Pipeline 3 — most impactful struggle nodes by pageRank."""
    return _run("struggle_pagerank", child_id=child_id)


def attention_trend(child_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Pipeline 3 — attention-window trend over the last N sessions."""
    return _run("attention_trend", child_id=child_id, limit=limit)
