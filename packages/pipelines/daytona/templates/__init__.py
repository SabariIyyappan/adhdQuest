"""Game template library (shipped inside the Daytona snapshot).

`build_game(spec)` is the single entrypoint generated game.py calls. It constructs
one Level per spec entry using the mechanic registry, wires the score tracker, and
returns a runnable Flask/WebSocket game server.
"""

from __future__ import annotations

import os
from typing import Any

from .base_level import Level, LevelConfig
from .mechanics import MECHANIC_REGISTRY
from .score_tracker import ScoreTracker
from .server import GameServer


def build_game(spec: dict[str, Any]) -> GameServer:
    session_id = spec.get("session_id") or os.environ.get("SESSION_ID", "")
    tracker = ScoreTracker(session_id)

    levels: list[Level] = []
    for entry in spec["levels"]:
        config = LevelConfig(**{k: entry[k] for k in _CONFIG_KEYS if k in entry})
        mechanic_cls = MECHANIC_REGISTRY[entry["mechanic"]]
        levels.append(mechanic_cls(config, tracker))

    return GameServer(levels=levels, tracker=tracker, spec=spec)


_CONFIG_KEYS = (
    "level_index",
    "question_id",
    "question_text",
    "topic",
    "difficulty",
    "mechanic",
    "is_attention_checkpoint",
)

__all__ = ["build_game", "GameServer", "Level", "LevelConfig"]
