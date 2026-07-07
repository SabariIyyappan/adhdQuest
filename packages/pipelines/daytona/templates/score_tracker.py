"""Per-level scoring + event emission (runs inside the sandbox).

Emits Contract D session events to Butterbase. The durable actor consumes them,
maintains the authoritative fail counter, and triggers replans; this local counter
is only for in-game display.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx


class ScoreTracker:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.fail_count: dict[int, int] = {}
        self._endpoint = os.environ["BUTTERBASE_EVENTS_URL"]
        self._client = httpx.Client(timeout=10.0)

    def level_start(self, level_index: int) -> None:
        self.fail_count.setdefault(level_index, 0)
        self._emit("level_start", level_index)

    def level_complete(self, level_index: int, score: int = 0) -> None:
        self._emit("level_complete", level_index, {"score": score})

    def level_fail(self, level_index: int) -> None:
        self.fail_count[level_index] = self.fail_count.get(level_index, 0) + 1
        self._emit("level_fail", level_index, {"fail_count": self.fail_count[level_index]})

    def session_end(self) -> None:
        self._emit("session_end", -1)

    def _emit(self, event_type: str, level_index: int, payload: dict | None = None) -> None:
        self._client.post(
            self._endpoint,
            json={
                "session_id": self.session_id,
                "event_type": event_type,
                "level_index": level_index,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload or {},
            },
        )
