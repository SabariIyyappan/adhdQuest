"""In-memory stand-in for Person A's Butterbase (REST + KV + realtime + serverless).

Mirrors the surface of :class:`pipelines.common.butterbase.Butterbase` exactly so it
can be dropped in through the DI seam. Everything is stored in plain dicts; nothing
touches the network. Inserts synthesize a uuid ``id`` like Postgres would, and every
realtime publish is captured in :attr:`published` for assertions.

The ``youtube-lookup`` serverless function is emulated with the plan's attention-window
rules (§6 Feature 2) so Pipeline 2 can be exercised without a YouTube API key.
"""

from __future__ import annotations

import uuid
from typing import Any


class FakeButterbase:
    def __init__(self) -> None:
        # table name -> list of row dicts
        self.tables: dict[str, list[dict[str, Any]]] = {}
        # kv key -> (value, ttl_seconds)
        self.kv: dict[str, dict[str, Any]] = {}
        self.kv_ttls: dict[str, int | None] = {}
        # every realtime event published, in order: (channel, payload)
        self.published: list[tuple[str, dict[str, Any]]] = []
        # serverless calls, in order: (name, body)
        self.function_calls: list[tuple[str, dict[str, Any]]] = []
        # optional canned video for youtube-lookup; None => rule-based default
        self.youtube_video: dict[str, Any] | None = None

    # --- REST ---------------------------------------------------------
    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        stored = dict(row)
        stored.setdefault("id", str(uuid.uuid4()))
        self.tables.setdefault(table, []).append(stored)
        return stored

    def update(self, table: str, row_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        for stored in self.tables.get(table, []):
            if stored.get("id") == row_id:
                stored.update(patch)
                return stored
        raise KeyError(f"{table} row {row_id} not found")

    def select(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        rows = self.tables.get(table, [])
        if not filters:
            return list(rows)
        return [r for r in rows if all(str(r.get(k)) == str(v) for k, v in filters.items())]

    # --- KV -----------------------------------------------------------
    def kv_get(self, key: str) -> dict[str, Any] | None:
        return self.kv.get(key)

    def kv_set(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        self.kv[key] = dict(value)
        self.kv_ttls[key] = ttl_seconds

    # --- Realtime -----------------------------------------------------
    def publish(self, channel: str, payload: dict[str, Any]) -> None:
        self.published.append((channel, dict(payload)))

    # --- Serverless ---------------------------------------------------
    def call_function(self, name: str, body: dict[str, Any]) -> dict[str, Any]:
        self.function_calls.append((name, dict(body)))
        if name == "youtube-lookup":
            return {"video": self._youtube_lookup(body)}
        return {}

    # --- helpers ------------------------------------------------------
    def _youtube_lookup(self, body: dict[str, Any]) -> dict[str, Any] | None:
        """Emulate the Deno YouTube function. Attention-window filter from plan §6:
        < 120s -> no video; 120-300s -> <=2min clip; > 300s -> <=4min clip."""
        remaining = int(body.get("remaining_attention_seconds", 0))
        if remaining < 120:
            return None
        if self.youtube_video is not None:
            return self.youtube_video
        duration = 110 if remaining <= 300 else 230
        concept = body.get("concept_tag", "concept")
        return {
            "youtube_id": f"vid_{concept}",
            "title": f"Understanding {concept} (visual)",
            "thumbnail_url": f"https://i.ytimg.com/vi/vid_{concept}/hqdefault.jpg",
            "duration_seconds": duration,
            "url": f"https://youtu.be/vid_{concept}",
        }

    # --- convenience for tests ---------------------------------------
    def events_of(self, channel: str, event: str) -> list[dict[str, Any]]:
        return [p for ch, p in self.published if ch == channel and p.get("event") == event]
