"""Butterbase REST + realtime client used by pipeline output nodes.

Pipelines never touch Postgres directly — Person A owns the schema. All writes go
through the auto-REST API or serverless functions using the service key.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class Butterbase:
    def __init__(self, base_url: str | None = None, service_key: str | None = None) -> None:
        self._base = (base_url or settings.butterbase_url).rstrip("/")
        self._key = service_key or settings.butterbase_service_key
        self._client = httpx.Client(
            base_url=self._base,
            headers={"Authorization": f"Bearer {self._key}"},
            timeout=30.0,
        )

    # --- REST ---------------------------------------------------------
    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(f"/rest/{table}", json=row).raise_for_status().json()

    def update(self, table: str, row_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return (
            self._client.patch(f"/rest/{table}?id=eq.{row_id}", json=patch)
            .raise_for_status()
            .json()
        )

    def select(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        query = "&".join(f"{k}=eq.{v}" for k, v in filters.items())
        return self._client.get(f"/rest/{table}?{query}").raise_for_status().json()

    # --- KV -----------------------------------------------------------
    def kv_get(self, key: str) -> dict[str, Any] | None:
        resp = self._client.get(f"/kv/{key}")
        return resp.json() if resp.status_code == 200 else None

    def kv_set(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        params = {"ttl": ttl_seconds} if ttl_seconds else {}
        self._client.put(f"/kv/{key}", json=value, params=params).raise_for_status()

    # --- Realtime -----------------------------------------------------
    def publish(self, channel: str, payload: dict[str, Any]) -> None:
        """Push a realtime event (Contract C) on a session channel."""
        self._client.post(f"/realtime/{channel}", json=payload).raise_for_status()

    # --- Serverless ---------------------------------------------------
    def call_function(self, name: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(f"/functions/{name}", json=body).raise_for_status().json()
