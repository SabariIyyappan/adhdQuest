"""Unit tests for the deterministic game-spec ordering rules (plan §6 Feature 1).

These exercise pure logic with no sponsor I/O, so they run without any live services.
"""

from __future__ import annotations

from pipelines.nodes.ner_node import TaggedQuestion
from pipelines.pipeline1_ingestion import game_spec


def _q(qid: str, topic: str, difficulty: int) -> TaggedQuestion:
    return TaggedQuestion(question_id=qid, text=f"q{qid}", topic=topic, difficulty=difficulty)


def test_default_order_is_easy_to_hard() -> None:
    questions = [_q("a", "division", 4), _q("b", "addition", 1), _q("c", "fractions", 3)]
    spec = game_spec.generate(
        questions=questions,
        metadata={"total_questions": 3},
        prior_context={"struggle_topics": []},
        profile={"attention_baseline_minutes": 15},
    )
    difficulties = [lvl["difficulty"] for lvl in spec["levels"]]
    assert difficulties == sorted(difficulties)


def test_struggle_topics_are_front_loaded() -> None:
    questions = [_q("a", "addition", 1), _q("b", "fractions", 3), _q("c", "division", 2)]
    spec = game_spec.generate(
        questions=questions,
        metadata={"total_questions": 3},
        prior_context={"struggle_topics": ["fractions"]},
        profile={"attention_baseline_minutes": 15},
    )
    assert spec["levels"][0]["topic"] == "fractions"


def test_load_category_from_avg_difficulty() -> None:
    light = game_spec.score_assignment([_q("a", "addition", 1), _q("b", "addition", 1)])
    heavy = game_spec.score_assignment([_q("a", "fractions", 5), _q("b", "division", 4)])
    assert light["estimated_attention_load"] == "light"
    assert heavy["estimated_attention_load"] == "heavy"
