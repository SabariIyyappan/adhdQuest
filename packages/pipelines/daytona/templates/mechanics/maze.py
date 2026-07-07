"""Maze mechanic — used for division (navigate to the correct quotient)."""

from __future__ import annotations

from typing import Any

from ..base_level import Level


class MazeLevel(Level):
    def render(self) -> dict[str, Any]:
        return {
            "mechanic": "maze",
            "prompt": self.config.question_text,
            "grid": self.config.params.get("grid", []),
            "exits": self.config.params.get("exits", []),  # each tagged with a candidate answer
        }

    def check_answer(self, answer: Any) -> bool:
        return str(answer) == str(self.config.params.get("correct"))
