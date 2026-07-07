"""Base level scaffolding shared by every game mechanic.

A concrete mechanic subclasses :class:`Level`, implements ``render`` and
``check_answer``, and inherits fail-counting + event emission. This lives inside the
Daytona snapshot so generated game code only needs to fill in mechanic specifics.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from .score_tracker import ScoreTracker


@dataclass
class LevelConfig:
    level_index: int
    question_id: str
    question_text: str
    topic: str
    difficulty: int
    mechanic: str
    is_attention_checkpoint: bool = False
    params: dict[str, Any] = field(default_factory=dict)


class Level(abc.ABC):
    """One playable level. Emits Contract D session events via the score tracker."""

    def __init__(self, config: LevelConfig, tracker: ScoreTracker) -> None:
        self.config = config
        self.tracker = tracker

    def start(self) -> None:
        self.tracker.level_start(self.config.level_index)

    def submit(self, answer: Any) -> bool:
        """Grade an answer; emit complete/fail. Returns True on correct."""
        correct = self.check_answer(answer)
        if correct:
            self.tracker.level_complete(self.config.level_index)
        else:
            self.tracker.level_fail(self.config.level_index)
        return correct

    @abc.abstractmethod
    def render(self) -> dict[str, Any]:
        """Return a serializable scene the canvas front-end draws."""

    @abc.abstractmethod
    def check_answer(self, answer: Any) -> bool:
        """Return whether the submitted answer solves this level."""
