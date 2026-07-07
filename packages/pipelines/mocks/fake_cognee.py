"""In-memory stand-in for Person A's Cognee client (child memory).

Exposes the same async methods the pipeline nodes call on
``backend.cognee.client``: ``recall``, ``remember``, ``cognify``, ``memify``,
``graph_qa``. Memory is per-child; ``remember`` appends session JSON and the
recall/QA methods reflect what has been ingested, so cross-session personalization
(front-loading struggle topics) can be exercised deterministically.

Seed a warm child up front with :meth:`seed`.
"""

from __future__ import annotations

from typing import Any


class FakeCognee:
    def __init__(self) -> None:
        # child_id -> list of remembered session_json dicts
        self.sessions: dict[str, list[dict[str, Any]]] = {}
        # child_id -> prior_context returned by recall (seeded or derived)
        self._seeded: dict[str, dict[str, Any]] = {}
        self.cognify_calls: list[str] = []
        self.memify_calls: list[str] = []

    def seed(self, child_id: str, prior_context: dict[str, Any]) -> None:
        """Pre-load a rich behavioral profile so recall returns it (a warm child)."""
        self._seeded[child_id] = prior_context

    def dataset_name(self, child_id: str) -> str:
        return f"child_{child_id}"

    async def recall(
        self, child_id: str, query: str = "learning patterns and attention history"
    ) -> dict[str, Any]:
        if child_id in self._seeded:
            ctx = dict(self._seeded[child_id])
        else:
            ctx = self._derive_context(child_id)
        ctx.setdefault("struggle_topics", [])
        ctx.setdefault("attention_window_minutes", None)
        ctx.setdefault("preferred_explanation_style", None)
        ctx.setdefault("last_session_summary", None)
        ctx.setdefault("medication_correlation", None)
        return ctx

    async def remember(self, session_json: dict[str, Any], child_id: str) -> None:
        self.sessions.setdefault(child_id, []).append(session_json)

    async def cognify(self, child_id: str) -> None:
        self.cognify_calls.append(child_id)

    async def memify(self, child_id: str) -> None:
        self.memify_calls.append(child_id)

    async def graph_qa(self, child_id: str, question: str) -> dict[str, Any]:
        n = len(self.sessions.get(child_id, []))
        return {
            "answer": f"Across {n} session(s), progress is trending steadily.",
            "citations": [s.get("session_id") for s in self.sessions.get(child_id, [])],
        }

    async def forget(self, child_id: str) -> None:
        self.sessions.pop(child_id, None)
        self._seeded.pop(child_id, None)

    # --- helpers ------------------------------------------------------
    def _derive_context(self, child_id: str) -> dict[str, Any]:
        """Infer struggle topics from remembered sessions (topics that were failed)."""
        struggle: set[str] = set()
        for s in self.sessions.get(child_id, []):
            for ev in s.get("replan_events", []):
                tag = (ev.get("payload") or {}).get("concept_tag")
                if tag:
                    struggle.add(tag)
        return {"struggle_topics": sorted(struggle)}
