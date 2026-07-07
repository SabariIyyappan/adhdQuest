"""Quest mechanic — used for word problems (dialogue-style answer paths)."""

from __future__ import annotations

from typing import Any

from ..base_level import Level


class QuestLevel(Level):
    def render(self) -> dict[str, Any]:
        return {
            "mechanic": "quest",
            "story": self.config.question_text,
            "choices": self.config.params.get("choices", []),
        }

    def check_answer(self, answer: Any) -> bool:
        return answer == self.config.params.get("correct_choice")
