"""NER node — raw text -> tagged questions (Pipeline 1, step 2).

Splits the assignment into question blocks and tags each with operation type and a
1–5 difficulty estimate based on operation complexity and step count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OperationType = Literal[
    "addition", "subtraction", "multiplication", "division",
    "fractions", "decimals", "word_problem",
]


@dataclass
class TaggedQuestion:
    question_id: str
    text: str
    topic: OperationType
    difficulty: int  # 1..5


def run(raw_text: str) -> list[TaggedQuestion]:
    questions: list[TaggedQuestion] = []
    for block in _split_into_question_blocks(raw_text):
        topic = _classify_operation(block)
        questions.append(
            TaggedQuestion(
                question_id=_new_id(),
                text=block,
                topic=topic,
                difficulty=_estimate_difficulty(block, topic),
            )
        )
    return questions


def _split_into_question_blocks(text: str) -> list[str]:
    # TODO(Person B): sentence/block segmentation + question detection.
    raise NotImplementedError


def _classify_operation(block: str) -> OperationType:
    raise NotImplementedError


def _estimate_difficulty(block: str, topic: OperationType) -> int:
    raise NotImplementedError


def _new_id() -> str:
    import uuid

    return str(uuid.uuid4())
