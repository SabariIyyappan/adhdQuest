"""Flask + WebSocket game server (runs inside the sandbox).

Renders the game to an HTML canvas so the preview URL embeds cleanly in the parent's
iframe (plan §10 risk register — avoids raw pygame windows). Supports two entrypoints:
`--validate` (headless: construct every level, exit non-zero on any error) and normal
serve mode used behind Daytona's `getPreviewLink`.
"""

from __future__ import annotations

import sys
from typing import Any

from .base_level import Level
from .score_tracker import ScoreTracker


class GameServer:
    def __init__(self, levels: list[Level], tracker: ScoreTracker, spec: dict[str, Any]) -> None:
        self.levels = levels
        self.tracker = tracker
        self.spec = spec

    def validate(self) -> int:
        """Headless self-check used by the Daytona build critic loop."""
        try:
            for level in self.levels:
                level.render()  # every mechanic must render without error
        except Exception as exc:  # noqa: BLE001 - surface to the critic agent via stderr
            print(f"level validation failed: {exc}", file=sys.stderr)
            return 1
        return 0

    def run(self) -> None:
        """Serve the game. Flask app + WebSocket wiring omitted from scaffolding."""
        if "--validate" in sys.argv:
            sys.exit(self.validate())
        # TODO(Person B): start Flask app on GAME_PREVIEW_PORT, stream canvas over WS.
        raise NotImplementedError("bind Flask + websocket serving")
