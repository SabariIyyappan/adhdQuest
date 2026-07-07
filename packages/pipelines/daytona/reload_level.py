"""Hot-reload a single level without restarting the game process.

Called inside the sandbox by Pipeline 2's live-rewrite node:
`python reload_level.py <level_index>`. Reads the freshly-uploaded `level_{N}.py`,
swaps it into the running game's level list, and notifies connected clients over the
WebSocket so the child continues from where they left off.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def reload_level(level_index: int) -> None:
    module_path = Path(f"level_{level_index}.py")
    if not module_path.exists():
        raise FileNotFoundError(module_path)

    spec = importlib.util.spec_from_file_location(f"level_{level_index}", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # TODO(Person B): hand `module.build_level()` to the running GameServer via an
    # IPC/socket hook and broadcast a "level_reloaded" WS event to the game frame.


if __name__ == "__main__":
    reload_level(int(sys.argv[1]))
