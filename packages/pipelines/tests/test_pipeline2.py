"""Pipeline 2 (struggle replan) tests: strategy selection, video gating, side effects."""

from __future__ import annotations

import uuid

from pipelines.pipeline2_replan import pipeline as p2
from pipelines.pipeline2_replan import strategy


def _seed_active_session(bb, child_id: str, sandbox_id: str = "sbx_test") -> None:
    bb.kv_set(f"session:{child_id}:active", {"sandbox_id": sandbox_id})


def _request(child_id: str, session_id: str, **over) -> dict:
    base = {
        "child_id": child_id,
        "session_id": session_id,
        "current_level_index": 4,
        "concept_tag": "fractions",
        "time_elapsed_seconds": 300,
        "attention_baseline_seconds": 15 * 60,
        "grade_level": 5,
    }
    base.update(over)
    return base


# --- strategy decision (pure) ----------------------------------------

def test_strategy_prerequisite_inject_when_one_step() -> None:
    plan = strategy.decide(
        prerequisite_path=["fractions_basics", "fractions"],
        remaining_attention_seconds=600,
        concept_tag="fractions",
        level_index=4,
    )
    assert plan["strategy"] == "prerequisite_inject"
    assert plan["include_video"] is True


def test_strategy_reorder_when_far() -> None:
    plan = strategy.decide(
        prerequisite_path=["a", "b", "c", "fractions"],
        remaining_attention_seconds=600,
        concept_tag="fractions",
        level_index=4,
    )
    assert plan["strategy"] == "reorder"


def test_strategy_confidence_builder_when_attention_low() -> None:
    plan = strategy.decide(
        prerequisite_path=["fractions_basics", "fractions"],
        remaining_attention_seconds=60,
        concept_tag="fractions",
        level_index=4,
    )
    assert plan["strategy"] == "confidence_builder"
    assert plan["include_video"] is False


# --- full pipeline 2 --------------------------------------------------

def test_pipeline2_publishes_replan_with_video(sponsors) -> None:
    child_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    _seed_active_session(bb, child_id)

    out = p2.run(_request(child_id, session_id))
    assert out["replan_applied"] is True

    replan = bb.events_of(f"child:{child_id}:session", "replan")[-1]
    assert replan["trigger_level"] == 4
    assert replan["video"] is not None
    assert replan["video"]["duration_seconds"] <= 240


def test_pipeline2_persists_event_and_video(sponsors) -> None:
    child_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    _seed_active_session(bb, child_id)

    p2.run(_request(child_id, session_id))
    assert bb.select("session_events", session_id=session_id, event_type="replan_triggered")
    assert bb.select("video_recommendations", session_id=session_id)


def test_pipeline2_hot_reloads_sandbox_level(sponsors) -> None:
    child_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb, daytona = sponsors["butterbase"], sponsors["daytona"]
    _seed_active_session(bb, child_id, sandbox_id="sbx_warm")

    p2.run(_request(child_id, session_id, current_level_index=4))
    sandbox = daytona.sandboxes["sbx_warm"]
    assert "level_4.py" in sandbox.files
    assert any("reload_level.py 4" in c for c in sandbox.commands)


def test_pipeline2_no_video_when_attention_exhausted(sponsors) -> None:
    child_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    _seed_active_session(bb, child_id)

    # remaining = 900 - 850 = 50s (< 120) -> confidence_builder, no video.
    p2.run(_request(child_id, session_id, time_elapsed_seconds=850))
    replan = bb.events_of(f"child:{child_id}:session", "replan")[-1]
    assert replan["strategy"] == "confidence_builder"
    assert replan["video"] is None
    assert not bb.select("video_recommendations", session_id=session_id)


def test_pipeline2_short_video_for_medium_attention(sponsors) -> None:
    child_id, session_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    _seed_active_session(bb, child_id)

    # remaining = 900 - 700 = 200s (120..300) -> <=2min clip.
    p2.run(_request(child_id, session_id, time_elapsed_seconds=700))
    replan = bb.events_of(f"child:{child_id}:session", "replan")[-1]
    assert replan["video"] is not None
    assert replan["video"]["duration_seconds"] <= 120
