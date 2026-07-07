"""End-to-end local runner for the three ADHDQuest pipelines (Person B).

Drives the full loop with Person A's services mocked in-process (no network, no
sponsor SDKs): PDF -> game (Pipeline 1) -> simulated gameplay with a 3-fail struggle
-> replan (Pipeline 2) -> session end -> memory + report (Pipeline 3). Run it to see
the whole spine work and to eyeball the Contract B/C/D/E payloads.

    python run_local.py                 # cold child (first session)
    python run_local.py --warm          # child Cognee already knows (fractions)

This is the local counterpart to deploying the .pipe canvases on RocketRide Cloud.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

# Windows consoles default to cp1252; force UTF-8 so em dashes/× render (docs §Windows).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pipelines import mocks
from pipelines.pipeline1_ingestion import pipeline as p1
from pipelines.pipeline2_replan import pipeline as p2
from pipelines.pipeline3_memory_report import pipeline as p3

FIXTURE = Path(__file__).parent / "fixtures" / "sample_worksheet.txt"


def _hr(title: str) -> None:
    print("\n" + "=" * 68 + f"\n  {title}\n" + "=" * 68)


def _dump(label: str, obj: Any) -> None:
    print(f"\n{label}:\n" + json.dumps(obj, indent=2, default=str))


def simulate_gameplay(bb: Any, session_id: str, level_map: list[dict[str, Any]]) -> tuple[int, str]:
    """Emit Contract D session events for a run where the child breezes through the
    early levels, then fails one fraction level 3× (triggering a replan). Returns the
    struggle level index and its concept tag."""
    struggle = next((lvl for lvl in level_map if lvl["topic"] == "fractions"), level_map[-1])
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
            for attempt in range(1, 4):  # three failures -> replan trigger
                emit("level_fail", idx, time_on_level_seconds=40, fail_count=attempt)
            emit("level_complete", idx, time_on_level_seconds=35, score=600)
        else:
            emit("level_complete", idx, time_on_level_seconds=30, score=900)
    return struggle_idx, concept


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warm", action="store_true", help="seed prior Cognee memory")
    args = parser.parse_args()

    child_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())

    installed = mocks.install_all()
    bb: Any = installed["butterbase"]
    cognee: Any = installed["cognee"]
    daytona: Any = installed["daytona"]

    if args.warm:
        cognee.seed(child_id, {"struggle_topics": ["fractions"], "attention_window_minutes": 12})

    try:
        # ---- Pipeline 1: PDF -> personalized game --------------------
        _hr("PIPELINE 1 — Ingestion & Game Generation")
        result = p1.run(
            {
                "child_id": child_id,
                "assignment_id": assignment_id,
                "pdf_storage_url": str(FIXTURE),
                "child_profile": {"grade": 5, "attention_baseline_minutes": 15},
            }
        )
        _dump("Contract B (Pipeline 1 result)", result)
        session_id = result["session_id"]
        print(f"\nRealtime pushed: {[p['event'] for _, p in bb.published]}")
        print(f"Level order (topic): {[l['topic'] for l in result['level_map']]}")

        # Simulate Person A persisting the questions rows from the level_map.
        for lvl in result["level_map"]:
            bb.insert(
                "questions",
                {
                    "assignment_id": assignment_id,
                    "level_index": lvl["level_index"],
                    "operation_type": lvl["topic"],
                    "difficulty": lvl["difficulty"],
                },
            )

        # ---- Simulated gameplay -> struggle --------------------------
        _hr("GAMEPLAY — simulated session events (Contract D)")
        struggle_idx, concept = simulate_gameplay(bb, session_id, result["level_map"])
        print(f"Child failed level {struggle_idx} ({concept}) 3× — replan triggers.")

        # ---- Pipeline 2: struggle replan ----------------------------
        _hr("PIPELINE 2 — Struggle Replan")
        replan = p2.run(
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
        _dump("Pipeline 2 result", replan)
        replan_event = bb.events_of(f"child:{child_id}:session", "replan")[-1]
        _dump("Contract C (replan realtime event)", replan_event)

        # ---- Session end -> Pipeline 3 ------------------------------
        _hr("PIPELINE 3 — Memory Ingestion & Report")
        outcome = p3.run({"child_id": child_id, "session_id": session_id})
        stored_report = bb.tables["reports"][-1]["report_json"]
        _dump("Contract E (report JSON)", stored_report)
        print(f"\nReport stored: {outcome['report_id']}")

        # ---- Assertions on sponsor side effects ---------------------
        _hr("SPONSOR SIDE-EFFECTS")
        print(f"Daytona sandboxes created: {list(daytona.sandboxes)}")
        print(f"Daytona sandbox stopped:   {[s.stopped for s in daytona.sandboxes.values()]}")
        cognee_ok = cognee.cognify_calls == cognee.memify_calls == [child_id]
        print(f"Cognee remember/cognify/memify ran for child: {cognee_ok}")
        print(f"Realtime events published: {[p['event'] for _, p in bb.published]}")
        print("\nOK — full three-pipeline loop completed locally.")
    finally:
        mocks.uninstall_all()


if __name__ == "__main__":
    main()
