"""Daytona custom nodes — sandbox lifecycle (Pipeline 1 build, Pipeline 2 rewrite).

Wraps the Daytona SDK. The agentic write -> run -> observe -> critic loop lives in
:func:`build_game`; live in-place edits live in :func:`rewrite_level`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from daytona_sdk import Daytona  # type: ignore

from ..common.config import settings

_MAX_BUILD_ITERATIONS = 3
_daytona = Daytona(api_key=settings.daytona_api_key, api_url=settings.daytona_api_url)


@dataclass
class BuildResult:
    game_url: str
    sandbox_id: str


def build_game(game_spec: dict[str, Any], game_code: str) -> BuildResult:
    """Create a warm sandbox from the snapshot, write the game, validate it runs,
    and return a live preview URL. A critic agent repairs failures up to 3 times."""
    sandbox = _daytona.create(
        snapshot=settings.daytona_snapshot,
        language="python",
        resources={"cpu": 1, "memory": 2, "disk": 4},
        auto_stop_interval=60,
    )
    sandbox.fs.upload_file(json.dumps(game_spec).encode(), "game_spec.json")

    code = game_code
    for _ in range(_MAX_BUILD_ITERATIONS):
        sandbox.fs.upload_file(code.encode(), "game.py")
        result = sandbox.process.code_run("python game.py --validate")
        if result.exit_code == 0:
            url = sandbox.get_preview_link(port=settings.game_preview_port)
            return BuildResult(game_url=url, sandbox_id=sandbox.id)
        code = _critic_repair(code, result.stderr)

    raise RuntimeError("game failed to validate after max build iterations")


def rewrite_level(sandbox_id: str, level_index: int, level_code: str) -> None:
    """Pipeline 2 — reconnect to the warm sandbox and hot-reload a single level."""
    sandbox = _daytona.get(sandbox_id)
    sandbox.fs.upload_file(level_code.encode(), f"level_{level_index}.py")
    sandbox.process.exec(f"python reload_level.py {level_index}")


def stop(sandbox_id: str) -> None:
    """Pipeline 3 — pause the sandbox at session end, preserving filesystem state."""
    _daytona.get(sandbox_id).stop()


def _critic_repair(code: str, stderr: str) -> str:
    """Ask the strong model to fix the game code given the runtime error."""
    # TODO(Person B): call Butterbase AI gateway (task=game_spec tier) with code+stderr.
    raise NotImplementedError("bind critic agent to AI gateway")
