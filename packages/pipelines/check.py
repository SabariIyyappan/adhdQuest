"""Setup + wiring check for the ADHDQuest pipelines (Person B).

RocketRide's mandatory checklist asks for a check program. This one verifies the
things that break silently without a live server:

  1. every pipeline module + node imports (DI seam keeps this SDK-free),
  2. the .pipe canvas files are valid JSON and follow the field-order rules,
  3. the mock sponsor layer wires in and the three pipelines run end-to-end,
  4. which live credentials are configured vs. still missing (informational).

Run: ``python -m pipelines.check``. Exit code is non-zero if any hard check fails.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
PIPE_DIR = ROOT / "pipes"

_ok = "[OK]  "
_bad = "[FAIL]"
_info = "[..]  "

failures: list[str] = []


def check_imports() -> None:
    print("\n1) Module imports")
    mods = [
        "pipelines.common.providers",
        "pipelines.common.ai_gateway",
        "pipelines.nodes.ocr_node",
        "pipelines.nodes.ner_node",
        "pipelines.nodes.cognee_nodes",
        "pipelines.nodes.daytona_node",
        "pipelines.nodes.neo4j_gds_node",
        "pipelines.nodes.youtube_node",
        "pipelines.pipeline1_ingestion.pipeline",
        "pipelines.pipeline2_replan.pipeline",
        "pipelines.pipeline3_memory_report.pipeline",
    ]
    import importlib

    for mod in mods:
        try:
            importlib.import_module(mod)
            print(f"  {_ok}{mod}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {_bad}{mod}: {exc}")
            failures.append(f"import {mod}")


def check_pipes() -> None:
    print("\n2) Pipeline .pipe files")
    if not PIPE_DIR.exists():
        print(f"  {_bad}missing {PIPE_DIR}")
        failures.append("pipes dir")
        return
    pipes = sorted(PIPE_DIR.glob("*.pipe"))
    if not pipes:
        print(f"  {_bad}no .pipe files found in {PIPE_DIR}")
        failures.append("no pipes")
    seen_ids: set[str] = set()
    for pipe in pipes:
        try:
            raw = pipe.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"  {_bad}{pipe.name}: invalid JSON ({exc})")
            failures.append(f"{pipe.name} json")
            continue
        first_key = next(iter(data))
        problems = []
        if first_key != "components":
            problems.append("'components' must be the first field")
        pid = data.get("project_id", "")
        if not pid or pid.startswith("${"):
            problems.append("project_id must be a literal GUID")
        if pid in seen_ids:
            problems.append("duplicate project_id across pipes")
        seen_ids.add(pid)
        ids = [c["id"] for c in data.get("components", [])]
        if len(ids) != len(set(ids)):
            problems.append("component ids not unique")
        if problems:
            print(f"  {_bad}{pipe.name}: {'; '.join(problems)}")
            failures.append(f"{pipe.name} structure")
        else:
            print(f"  {_ok}{pipe.name} ({len(ids)} components)")


def check_end_to_end() -> None:
    print("\n3) Mocked end-to-end (Pipeline 1 -> 2 -> 3)")
    try:
        from pipelines.tests.helpers import run_full_loop

        report = run_full_loop()
        assert report["bottleneck_concept"], "no bottleneck concept in report"
        print(f"  {_ok}full loop ran; bottleneck = {report['bottleneck_concept']}")
    except Exception as exc:  # noqa: BLE001
        print(f"  {_bad}end-to-end failed: {exc}")
        failures.append("end-to-end")


def check_credentials() -> None:
    print("\n4) Live credentials (informational — mocks cover these locally)")
    keys = [
        "ROCKETRIDE_URI",
        "ROCKETRIDE_APIKEY",
        "BUTTERBASE_URL",
        "BUTTERBASE_SERVICE_KEY",
        "BUTTERBASE_AI_GATEWAY_URL",
        "NEO4J_URI",
        "NEO4J_PASSWORD",
        "DAYTONA_API_KEY",
    ]
    for key in keys:
        state = "set" if os.getenv(key) else "missing (mocked)"
        print(f"  {_info}{key}: {state}")


def main() -> int:
    print("=" * 60)
    print("  ADHDQuest pipelines — setup check (Person B)")
    print("=" * 60)
    check_imports()
    check_pipes()
    check_end_to_end()
    check_credentials()

    print("\n" + "=" * 60)
    if failures:
        print(f"  RESULT: {len(failures)} check(s) FAILED -> {failures}")
        return 1
    print("  RESULT: all hard checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
