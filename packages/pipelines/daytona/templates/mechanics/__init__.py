"""Game mechanic registry.

One renderer per mechanic (plan §6 Feature 1). Generated game specs reference these
by name; the template factory looks them up here.
"""

from __future__ import annotations

from ..base_level import Level
from .matching import MatchingLevel
from .maze import MazeLevel
from .puzzle import PuzzleLevel
from .quest import QuestLevel
from .speed_round import SpeedRoundLevel

MECHANIC_REGISTRY: dict[str, type[Level]] = {
    "maze": MazeLevel,
    "matching": MatchingLevel,
    "quest": QuestLevel,
    "speed_round": SpeedRoundLevel,
    "puzzle": PuzzleLevel,
}

__all__ = ["MECHANIC_REGISTRY"]
