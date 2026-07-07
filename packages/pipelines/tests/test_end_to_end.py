"""Full three-pipeline loop and cross-cutting invariants."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from pipelines.common import providers
from tests.helpers import run_full_loop

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "contracts" / "schemas"


def test_full_loop_cold_child_produces_report() -> None:
    report = run_full_loop(warm=False)
    assert report["session_summary"]["levels_total"] > 0
    assert report["bottleneck_concept"]
    assert report["parent_summary"] and report["doctor_narrative"]


def test_full_loop_warm_child_produces_report() -> None:
    report = run_full_loop(warm=True)
    assert report["bottleneck_concept"] == "fractions"


def test_report_attention_arc_is_monotonic_minutes() -> None:
    report = run_full_loop()
    minutes = [p["minute"] for p in report["attention_arc"]]
    assert minutes == sorted(minutes)
    assert all(p["errors"] >= 0 for p in report["attention_arc"])


def test_providers_reset_after_loop() -> None:
    run_full_loop()
    # After the loop tears down, no overrides should leak into the next run.
    assert providers._overrides == {}


def test_next_session_recommendations_shape() -> None:
    report = run_full_loop()
    rec = report["next_session_recommendations"]
    assert rec["suggested_duration_minutes"] >= 12
    assert isinstance(rec["prioritize_concepts"], list)
