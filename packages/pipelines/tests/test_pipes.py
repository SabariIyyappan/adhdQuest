"""Validate the .pipe canvas files against RocketRide's structural rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PIPE_DIR = Path(__file__).resolve().parents[1] / "pipes"
_PIPES = sorted(_PIPE_DIR.glob("*.pipe"))


def test_three_pipes_exist() -> None:
    names = {p.name for p in _PIPES}
    assert names == {
        "pipeline1_ingestion.pipe",
        "pipeline2_replan.pipe",
        "pipeline3_memory_report.pipe",
    }


@pytest.mark.parametrize("pipe", _PIPES, ids=lambda p: p.name)
def test_pipe_is_valid_json_with_field_order(pipe: Path) -> None:
    data = json.loads(pipe.read_text(encoding="utf-8"))
    assert next(iter(data)) == "components", "'components' must be first"
    assert data["version"] == 1
    assert "viewport" in data


@pytest.mark.parametrize("pipe", _PIPES, ids=lambda p: p.name)
def test_pipe_project_id_is_literal_guid(pipe: Path) -> None:
    pid = json.loads(pipe.read_text(encoding="utf-8"))["project_id"]
    assert not pid.startswith("${")
    assert len(pid) == 36 and pid.count("-") == 4


def test_pipe_project_ids_are_unique() -> None:
    ids = [json.loads(p.read_text(encoding="utf-8"))["project_id"] for p in _PIPES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("pipe", _PIPES, ids=lambda p: p.name)
def test_component_ids_unique_and_source_configured(pipe: Path) -> None:
    comps = json.loads(pipe.read_text(encoding="utf-8"))["components"]
    ids = [c["id"] for c in comps]
    assert len(ids) == len(set(ids))

    source = next(c for c in comps if c["provider"] == "webhook")
    for key in ("hideForm", "mode", "parameters", "type"):
        assert key in source["config"], f"source missing config.{key}"


@pytest.mark.parametrize("pipe", _PIPES, ids=lambda p: p.name)
def test_control_arrays_point_to_agent_not_reverse(pipe: Path) -> None:
    comps = {c["id"]: c for c in json.loads(pipe.read_text(encoding="utf-8"))["components"]}
    agent = comps["agent_rocketride_1"]
    # The agent itself must NOT carry a control array.
    assert "control" not in agent
    # LLM + memory + tools declare they are controlled BY the agent.
    for cid, comp in comps.items():
        if comp["provider"] in {"llm_anthropic", "memory_internal"} or comp["provider"].startswith("tool_"):
            assert comp.get("control"), f"{cid} missing control array"
            assert all(ctrl["from"] == "agent_rocketride_1" for ctrl in comp["control"])


@pytest.mark.parametrize("pipe", _PIPES, ids=lambda p: p.name)
def test_agent_consumes_questions_from_source(pipe: Path) -> None:
    comps = {c["id"]: c for c in json.loads(pipe.read_text(encoding="utf-8"))["components"]}
    agent_inputs = comps["agent_rocketride_1"]["input"]
    assert {"lane": "questions", "from": "webhook_1"} in agent_inputs
    response_inputs = comps["response_answers_1"]["input"]
    assert {"lane": "answers", "from": "agent_rocketride_1"} in response_inputs
