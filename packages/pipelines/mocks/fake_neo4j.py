"""In-memory stand-in for Person A's Neo4j + GDS.

Implements just enough of the ``neo4j`` driver surface that
``pipelines.nodes.neo4j_gds_node`` uses: ``driver.session()`` as a context manager
yielding an object with ``run(query, **params)`` -> iterable of records exposing
``.data()``. Queries are routed by matching the GDS procedure / return signature in
the Cypher text (the real named queries live in ``backend/neo4j/queries.cypher``),
so the node code runs unchanged.

Results are deterministic and configurable via public attributes so tests can pin
exact analytics without a live graph. Sensible defaults make end-to-end runs work.
"""

from __future__ import annotations

from typing import Any


class _FakeRecord:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def data(self) -> dict[str, Any]:
        return self._data


class _FakeSession:
    def __init__(self, driver: "FakeNeo4jDriver") -> None:
        self._driver = driver

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def run(self, query: str, **params: Any) -> list[_FakeRecord]:
        rows = self._driver.dispatch(query, params)
        return [_FakeRecord(r) for r in rows]


class FakeNeo4jDriver:
    def __init__(self) -> None:
        # (child_id, blocked_concept) -> ordered prerequisite concept names.
        self.prerequisite_paths: dict[tuple[str, str], list[str]] = {}
        # canned analytics rows (override in tests to pin exact output).
        self.bottleneck: list[dict[str, Any]] = [{"concept": "fractions", "score": 0.87}]
        self.struggle: list[dict[str, Any]] = [{"struggle_event": "se_1", "score": 0.5}]
        self.attention: list[dict[str, Any]] = []
        # every (query, params) dispatched, for assertions.
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def session(self) -> _FakeSession:
        return _FakeSession(self)

    def close(self) -> None:
        return None

    # --- routing ------------------------------------------------------
    def dispatch(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((query, dict(params)))
        q = query.lower()
        if "shortestpath.dijkstra" in q or "prerequisite_path" in q:
            return self._prerequisite_path(params)
        if "betweenness" in q:
            return list(self.bottleneck)
        if "pagerank" in q:
            return list(self.struggle)
        if "attention_window_minutes" in q or "attention_trend" in q:
            rows = list(self.attention)
            limit = params.get("limit")
            return rows[:limit] if isinstance(limit, int) else rows
        if "nodesimilarity" in q:
            return []
        return []

    def _prerequisite_path(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        child_id = params.get("child_id", "")
        blocked = params.get("blocked_concept", "")
        key = (child_id, blocked)
        if key in self.prerequisite_paths:
            path = self.prerequisite_paths[key]
        else:
            # Default: a one-step-away prerequisite (mastered ancestor -> blocked).
            path = [f"{blocked}_basics", blocked] if blocked else []
        return [{"prerequisite_path": path}]
