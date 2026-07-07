"""Pytest fixtures: install the sponsor mocks around each test that needs them."""

from __future__ import annotations

from typing import Any, Iterator

import pytest

from pipelines import mocks


@pytest.fixture
def sponsors() -> Iterator[dict[str, Any]]:
    """Inject fresh in-memory sponsor mocks; tear them down afterwards.

    Yields the dict of installed fakes: {butterbase, cognee, daytona, neo4j}.
    """
    installed = mocks.install_all()
    try:
        yield installed
    finally:
        mocks.uninstall_all()
