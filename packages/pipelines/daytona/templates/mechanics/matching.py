"""Matching mechanic — used for fractions (match equivalent fraction tiles)."""

from __future__ import annotations

from typing import Any

from ..base_level import Level


class MatchingLevel(Level):
    def render(self) -> dict[str, Any]:
        return {
            "mechanic": "matching",
            "prompt": self.config.question_text,
            "tiles": self.config.params.get("tiles", []),
        }

    def check_answer(self, answer: Any) -> bool:
        # answer: list of matched tile-id pairs.
        return sorted(map(tuple, answer)) == sorted(self.config.params.get("pairs", []))
