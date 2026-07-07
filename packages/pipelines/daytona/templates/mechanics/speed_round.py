"""Speed-round mechanic — used for addition/subtraction (time-limited scoring)."""

from __future__ import annotations

from typing import Any

from ..base_level import Level


class SpeedRoundLevel(Level):
    def render(self) -> dict[str, Any]:
        return {
            "mechanic": "speed_round",
            "prompt": self.config.question_text,
            "time_limit_seconds": self.config.params.get("time_limit_seconds", 30),
        }

    def check_answer(self, answer: Any) -> bool:
        return str(answer).strip() == str(self.config.params.get("correct")).strip()
