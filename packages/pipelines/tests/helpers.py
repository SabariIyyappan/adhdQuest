"""Shared test helpers: build a Contract-A request and drive the full loop.

Reused by both the pytest suite and ``pipelines.check`` so the end-to-end path has a
single definition. Everything runs against the in-memory sponsor mocks.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pipelines import mocks
from pipelines.pipeline1_ingestion import pipeline as p1
from pipelines.pipeline2_replan import pipeline as p2
from pipelines.pipeline3_memory_report import pipeline as p3

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_worksheet.txt"


def contract_a(child_id: str, assignment_id: str, *, grade: int = 5, baseline: int = 15) -> dict[str, Any]:
    return {
        "child_id": child_id,
        "assignment_id": assignment_id,
        "pdf_storage_url": str(FIXTURE),
        "child_profile": {"grade": grade, "attention_baseline_minutes": baseline},
    }


def persist_questions(bb: Any, assignment_id: str, level_map: list[dict[str, Any]]) -> None:
    """Simulate Person A persisting questions rows from the level_map."""
    for lvl in level_map:
        bb.insert(
            "questions",
            {
                "assignment_id": assignment_id,
                "level_index": lvl["level_index"],
                "operation_type": lvl["topic"],
                "difficulty": lvl["difficulty"],
            },
        )


def emit_gameplay(
    bb: Any, session_id: str, level_map: list[dict[str, Any]], *, struggle_topic: str = "fractions"
) -> tuple[int, str]:
    """Emit Contract D events: clean run except a 3-fail struggle on one topic."""
    struggle = next((lvl for lvl in level_map if lvl["topic"] == struggle_topic), level_map[-1])
    struggle_idx, concept = struggle["level_index"], struggle["topic"]

    def emit(event_type: str, level_index: int, **payload: Any) -> None:
        bb.insert(
            "session_events",
            {
                "session_id": session_id,
                "event_type": event_type,
                "level_index": level_index,
                "payload": payload,
            },
        )

    for lvl in level_map:
        idx = lvl["level_index"]
        emit("level_start", idx, time_on_level_seconds=0)
        if idx == struggle_idx:
            for attempt in range(1, 4):
                emit("level_fail", idx, time_on_level_seconds=40, fail_count=attempt)
            emit("level_complete", idx, time_on_level_seconds=35, score=600)
        else:
            emit("level_complete", idx, time_on_level_seconds=30, score=900)
    return struggle_idx, concept


def run_full_loop(*, warm: bool = False) -> dict[str, Any]:
    """Install mocks, run Pipeline 1 -> 2 -> 3, return the stored report JSON."""
    child_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    installed = mocks.install_all()
    bb: Any = installed["butterbase"]
    if warm:
        installed["cognee"].seed(child_id, {"struggle_topics": ["fractions"]})
    try:
        result = p1.run(contract_a(child_id, assignment_id))
        session_id = result["session_id"]
        persist_questions(bb, assignment_id, result["level_map"])
        struggle_idx, concept = emit_gameplay(bb, session_id, result["level_map"])
        p2.run(
            {
                "child_id": child_id,
                "session_id": session_id,
                "current_level_index": struggle_idx,
                "concept_tag": concept,
                "time_elapsed_seconds": 300,
                "attention_baseline_seconds": 15 * 60,
                "grade_level": 5,
            }
        )
        p3.run({"child_id": child_id, "session_id": session_id})
        return bb.tables["reports"][-1]["report_json"]
    finally:
        mocks.uninstall_all()
