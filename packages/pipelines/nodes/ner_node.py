"""NER node — raw text -> tagged questions (Pipeline 1, step 2).

Splits the assignment into question blocks and tags each with operation type and a
1–5 difficulty estimate based on operation complexity and step count.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Literal

OperationType = Literal[
    "addition", "subtraction", "multiplication", "division",
    "fractions", "decimals", "word_problem",
]

# Leading enumerators like "1.", "2)", "Q3:" that start a new question block.
_ENUMERATOR = re.compile(r"(?m)^\s*(?:Q\s*)?\d+\s*[\.\):]\s+")

# Keyword signals per operation (checked in priority order below).
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "fractions": ("fraction", "numerator", "denominator", "/", "½", "¼", "¾"),
    "decimals": ("decimal", "tenth", "hundredth"),
    "division": ("divide", "divided", "quotient", "÷", "shared equally", "split", "each"),
    "multiplication": ("multiply", "product", "times", "×", "*"),
    "subtraction": ("subtract", "minus", "difference", "less than", "take away", "left", "−"),
    "addition": ("add", "sum", "plus", "altogether", "in all", "total", "combined", "+"),
}

# Base difficulty by operation type (1 easiest — 5 hardest).
_BASE_DIFFICULTY: dict[str, int] = {
    "addition": 1,
    "subtraction": 1,
    "multiplication": 2,
    "decimals": 3,
    "division": 3,
    "word_problem": 3,
    "fractions": 4,
}


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
    """Segment an assignment into individual question blocks.

    Prefers numbered enumerators ("1.", "2)", "Q3:"); if none are present, falls
    back to one question per non-empty line, keeping only lines that look like a
    question (contain a digit, an operator, or a '?').
    """
    if not text or not text.strip():
        return []

    if _ENUMERATOR.search(text):
        parts = _ENUMERATOR.split(text)
        blocks = [_clean(p) for p in parts if _clean(p)]
        return blocks

    blocks = []
    for line in text.splitlines():
        cleaned = _clean(line)
        if cleaned and _looks_like_question(cleaned):
            blocks.append(cleaned)
    return blocks


def _clean(block: str) -> str:
    return re.sub(r"\s+", " ", block).strip()


def _looks_like_question(block: str) -> bool:
    return "?" in block or any(ch.isdigit() for ch in block) or bool(
        re.search(r"[+\-×÷*/]", block)
    )


def _classify_operation(block: str) -> OperationType:
    lowered = block.lower()

    # A prose question with no bare arithmetic operator reads as a word problem.
    if _is_word_problem(block, lowered):
        return "word_problem"

    # Bare arithmetic expressions ("20 - 8 = ?") — classify by the operator symbol.
    symbol_topic = _classify_symbol(block)
    if symbol_topic:
        return symbol_topic  # type: ignore[return-value]

    for topic, signals in _KEYWORDS.items():
        if any(sig in lowered for sig in signals):
            # Guard: "a/b" between digits is a fraction, not division.
            if topic == "division" and _has_fraction_slash(block):
                return "fractions"
            return topic  # type: ignore[return-value]

    if _has_fraction_slash(block):
        return "fractions"
    return "word_problem"


def _classify_symbol(block: str) -> str | None:
    """Detect the operation from a digit-operator-digit expression."""
    if re.search(r"\d\s*/\s*\d", block):
        return "fractions"
    if re.search(r"\d\s*÷\s*\d", block):
        return "division"
    if re.search(r"\d\s*[×*]\s*\d", block):
        return "multiplication"
    if re.search(r"\d\s*\+\s*\d", block):
        return "addition"
    if re.search(r"\d\s*[-−]\s*\d", block):
        return "subtraction"
    return None


def _is_word_problem(block: str, lowered: str) -> bool:
    word_count = len(re.findall(r"[A-Za-z]+", block))
    has_symbol = bool(re.search(r"\d\s*[+\-×÷*]\s*\d", block))
    narrative = word_count >= 6 and block.rstrip().endswith("?")
    return narrative and not has_symbol


def _has_fraction_slash(block: str) -> bool:
    return bool(re.search(r"\d+\s*/\s*\d+", block))


def _estimate_difficulty(block: str, topic: OperationType) -> int:
    difficulty = _BASE_DIFFICULTY.get(topic, 3)

    numbers = [int(n) for n in re.findall(r"\d+", block)]
    if any(n >= 100 for n in numbers):
        difficulty += 1
    # Multiple operators => multi-step problem.
    if len(re.findall(r"[+\-×÷*/]", block)) >= 2:
        difficulty += 1
    # Longer prose word problems carry more cognitive load.
    if topic == "word_problem" and len(re.findall(r"[A-Za-z]+", block)) >= 20:
        difficulty += 1

    return max(1, min(5, difficulty))


def _new_id() -> str:
    return str(uuid.uuid4())
