"""Pipeline 3 (memory + report) tests: assembly, report shape, side effects."""

from __future__ import annotations

import uuid

from pipelines.pipeline3_memory_report import assemble, pipeline as p3
from tests.helpers import emit_gameplay, persist_questions


def _setup_session(bb, *, child_id: str, with_medication: bool = False) -> tuple[str, list]:
    assignment_id = str(uuid.uuid4())
    sandbox_id = "sbx_p3"
    session = bb.insert(
        "sessions",
        {
            "child_id": child_id,
            "assignment_id": assignment_id,
            "sandbox_id": sandbox_id,
            "game_url": "https://x/",
            "status": "active",
        },
    )
    level_map = [
        {"level_index": 0, "topic": "addition", "difficulty": 1},
        {"level_index": 1, "topic": "division", "difficulty": 3},
        {"level_index": 2, "topic": "fractions", "difficulty": 4},
    ]
    persist_questions(bb, assignment_id, level_map)
    struggle_idx, _ = emit_gameplay(bb, session["id"], level_map, struggle_topic="fractions")
    # Simulate the Pipeline 2 replan event that a real struggle would have produced.
    bb.insert(
        "session_events",
        {
            "session_id": session["id"],
            "event_type": "replan_triggered",
            "level_index": struggle_idx,
            "payload": {"strategy": "prerequisite_inject"},
        },
    )
    if with_medication:
        bb.insert(
            "medication_logs",
            {
                "child_id": child_id,
                "medication_name": "methylphenidate",
                "time_delta_minutes": 45,
            },
        )
    return session["id"], level_map


def test_assemble_attention_arc_and_concept_performance(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb = sponsors["butterbase"]
    session_id, _ = _setup_session(bb, child_id=child_id)

    data = assemble.build(bb, child_id=child_id, session_id=session_id)
    # All three fails fall inside the first 5-minute window for this short session.
    assert data["attention_arc"][0] == {"minute": 0, "errors": 3}
    total_errors = sum(p["errors"] for p in data["attention_arc"])
    assert total_errors == 3
    # fractions had 3 fails + 1 complete = 4 attempts, fail_rate 0.75.
    frac = next(c for c in data["concept_performance"] if c["concept"] == "fractions")
    assert frac["fail_rate"] == 0.75
    assert frac["replan_triggered"] is True


def test_pipeline3_report_matches_contract_e(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb = sponsors["butterbase"]
    session_id, _ = _setup_session(bb, child_id=child_id)

    out = p3.run({"child_id": child_id, "session_id": session_id})
    report = bb.select("reports", id=out["report_id"])[0]["report_json"]

    assert set(report) == {
        "session_summary",
        "attention_arc",
        "concept_performance",
        "bottleneck_concept",
        "bottleneck_centrality_score",
        "parent_summary",
        "doctor_narrative",
        "next_session_recommendations",
        "medication_correlation",
    }
    assert report["parent_summary"]
    assert report["doctor_narrative"]
    assert report["bottleneck_concept"] == "fractions"


def test_pipeline3_marks_session_complete_and_publishes(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb = sponsors["butterbase"]
    session_id, _ = _setup_session(bb, child_id=child_id)

    p3.run({"child_id": child_id, "session_id": session_id})
    assert bb.select("sessions", id=session_id)[0]["status"] == "complete"
    assert bb.events_of(f"child:{child_id}:session", "session_end")


def test_pipeline3_runs_cognee_ingest_in_order(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb, cognee = sponsors["butterbase"], sponsors["cognee"]
    session_id, _ = _setup_session(bb, child_id=child_id)

    p3.run({"child_id": child_id, "session_id": session_id})
    assert cognee.sessions.get(child_id)  # remembered
    assert cognee.cognify_calls == [child_id]
    assert cognee.memify_calls == [child_id]


def test_pipeline3_stops_the_sandbox(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb, daytona = sponsors["butterbase"], sponsors["daytona"]
    session_id, _ = _setup_session(bb, child_id=child_id)

    p3.run({"child_id": child_id, "session_id": session_id})
    assert daytona.sandboxes["sbx_p3"].stopped is True


def test_pipeline3_medication_correlation_present(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb = sponsors["butterbase"]
    session_id, _ = _setup_session(bb, child_id=child_id, with_medication=True)

    out = p3.run({"child_id": child_id, "session_id": session_id})
    report = bb.select("reports", id=out["report_id"])[0]["report_json"]
    assert report["medication_correlation"] is not None
    assert report["medication_correlation"]["medication"] == "methylphenidate"


def test_pipeline3_no_medication_correlation_when_absent(sponsors) -> None:
    child_id = str(uuid.uuid4())
    bb = sponsors["butterbase"]
    session_id, _ = _setup_session(bb, child_id=child_id, with_medication=False)

    out = p3.run({"child_id": child_id, "session_id": session_id})
    report = bb.select("reports", id=out["report_id"])[0]["report_json"]
    assert report["medication_correlation"] is None
