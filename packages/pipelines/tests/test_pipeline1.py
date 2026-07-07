"""Pipeline 1 (ingestion & game generation) tests against the sponsor mocks."""

from __future__ import annotations

import uuid

import pytest

from pipelines import mocks
from pipelines.common import providers
from pipelines.nodes import daytona_node
from pipelines.pipeline1_ingestion import pipeline as p1
from tests.helpers import contract_a


def test_pipeline1_returns_contract_b(sponsors) -> None:
    child_id, assignment_id = str(uuid.uuid4()), str(uuid.uuid4())
    result = p1.run(contract_a(child_id, assignment_id))

    assert set(result) >= {
        "session_id",
        "game_url",
        "sandbox_id",
        "level_map",
        "estimated_session_minutes",
    }
    assert result["game_url"].startswith("https://")
    assert result["level_map"], "expected a non-empty level map"
    for entry in result["level_map"]:
        assert set(entry) == {"level_index", "question_id", "topic", "difficulty"}


def test_pipeline1_persists_session_and_kv(sponsors) -> None:
    child_id, assignment_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    result = p1.run(contract_a(child_id, assignment_id))

    sessions = bb.select("sessions", id=result["session_id"])
    assert sessions and sessions[0]["status"] == "active"
    assert sessions[0]["sandbox_id"] == result["sandbox_id"]

    state = bb.kv_get(f"session:{child_id}:active")
    assert state and state["sandbox_id"] == result["sandbox_id"]
    assert bb.kv_ttls[f"session:{child_id}:active"] == 2 * 60 * 60


def test_pipeline1_publishes_game_ready(sponsors) -> None:
    child_id, assignment_id = str(uuid.uuid4()), str(uuid.uuid4())
    bb = sponsors["butterbase"]
    result = p1.run(contract_a(child_id, assignment_id))

    events = bb.events_of(f"child:{child_id}:session", "game_ready")
    assert len(events) == 1
    assert events[0]["game_url"] == result["game_url"]
    assert events[0]["level_count"] == len(result["level_map"])


def test_pipeline1_default_order_is_easy_to_hard(sponsors) -> None:
    result = p1.run(contract_a(str(uuid.uuid4()), str(uuid.uuid4())))
    difficulties = [e["difficulty"] for e in result["level_map"]]
    assert difficulties == sorted(difficulties)


def test_pipeline1_warm_child_front_loads_struggle_topic(sponsors) -> None:
    child_id, assignment_id = str(uuid.uuid4()), str(uuid.uuid4())
    sponsors["cognee"].seed(child_id, {"struggle_topics": ["fractions"]})
    result = p1.run(contract_a(child_id, assignment_id))
    assert result["level_map"][0]["topic"] == "fractions"


def test_pipeline1_writes_game_files_to_sandbox(sponsors) -> None:
    result = p1.run(contract_a(str(uuid.uuid4()), str(uuid.uuid4())))
    sandbox = sponsors["daytona"].sandboxes[result["sandbox_id"]]
    assert "game_spec.json" in sandbox.files
    assert "game.py" in sandbox.files


# --- critic build loop (stress) --------------------------------------

def test_build_critic_repairs_until_valid() -> None:
    providers.set_provider("daytona", mocks.FakeDaytona(fail_validations=2))
    try:
        build = daytona_node.build_game({"levels": []}, "print('game')\n")
        sandbox = providers.get_daytona().sandboxes[build.sandbox_id]
        # 2 failed + 1 successful validate == 3 attempts.
        assert sandbox.validate_attempts == 3
        assert build.game_url
    finally:
        providers.reset_providers()


def test_build_raises_after_max_iterations() -> None:
    providers.set_provider("daytona", mocks.FakeDaytona(fail_validations=99))
    try:
        with pytest.raises(RuntimeError):
            daytona_node.build_game({"levels": []}, "print('game')\n")
    finally:
        providers.reset_providers()
