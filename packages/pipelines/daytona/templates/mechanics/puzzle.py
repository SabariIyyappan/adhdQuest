"""Puzzle mechanic — default/general (multiplication, decimals, checkpoints)."""

from __future__ import annotations

from typing import Any

from ..base_level import Level


class PuzzleLevel(Level):
    def render(self) -> dict[str, Any]:
        return {
            "mechanic": "puzzle",
            "prompt": self.config.question_text,
            "pieces": self.config.params.get("pieces", []),
            "is_breather": self.config.is_attention_checkpoint,
        }

    def check_answer(self, answer: Any) -> bool:
        return str(answer).strip() == str(self.config.params.get("correct")).strip()
