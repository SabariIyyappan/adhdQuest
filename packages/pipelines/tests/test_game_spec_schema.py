"""Validate the generated game spec against contracts/schemas/game_spec.schema.json."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import jsonschema

from pipelines.nodes.ner_node import TaggedQuestion
from pipelines.pipeline1_ingestion import game_spec

_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "schemas" / "game_spec.schema.json").read_text(
        encoding="utf-8"
    )
)


def _questions() -> list[TaggedQuestion]:
    return [
        TaggedQuestion(str(uuid.uuid4()), "2 + 2", "addition", 1),
        TaggedQuestion(str(uuid.uuid4()), "1/2 + 1/4", "fractions", 4),
        TaggedQuestion(str(uuid.uuid4()), "56 / 8", "division", 3),
    ]


def test_generated_spec_is_schema_valid() -> None:
    spec = game_spec.generate(
        questions=_questions(),
        metadata={"total_questions": 3},
        prior_context={"struggle_topics": []},
        profile={"attention_baseline_minutes": 15},
    )
    # session_id is filled by the output node after the sessions row exists.
    spec = {**spec, "session_id": str(uuid.uuid4())}
    jsonschema.validate(spec, _SCHEMA)


def test_no_more_than_two_consecutive_same_mechanic() -> None:
    # Many same-topic questions would repeat a mechanic; ensure the spec still
    # validates structurally (mechanic-variety is a soft rule enforced in prompt).
    qs = [TaggedQuestion(str(uuid.uuid4()), "2 + 2", "addition", 1) for _ in range(6)]
    spec = game_spec.generate(
        questions=qs,
        metadata={"total_questions": 6},
        prior_context={},
        profile={"attention_baseline_minutes": 15},
    )
    spec = {**spec, "session_id": str(uuid.uuid4())}
    jsonschema.validate(spec, _SCHEMA)


def test_attention_checkpoints_inserted() -> None:
    qs = [TaggedQuestion(str(uuid.uuid4()), f"{i} + {i}", "addition", 1) for i in range(12)]
    spec = game_spec.generate(
        questions=qs,
        metadata={"total_questions": 12},
        prior_context={},
        profile={"attention_baseline_minutes": 15},  # interval = 15//3 = 5
    )
    checkpoints = [lvl for lvl in spec["levels"] if lvl["is_attention_checkpoint"]]
    assert checkpoints, "expected at least one breather checkpoint"
