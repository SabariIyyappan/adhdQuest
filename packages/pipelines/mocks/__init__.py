"""In-memory mocks of Person A's endpoints and sponsor SDKs (local-first dev).

Person A owns Butterbase, Cognee, Neo4j, and (indirectly) the YouTube serverless
function; Person B owns Daytona. Until those live services exist, these fakes let
the three pipelines run and be stress-tested end-to-end with zero network I/O.

Wire them in with :func:`install_all`, which injects each fake through the
``common.providers`` DI seam. Call :func:`uninstall_all` (or use the pytest
``mocks`` fixture) to restore real providers.
"""

from __future__ import annotations

from ..common import providers
from .fake_butterbase import FakeButterbase
from .fake_cognee import FakeCognee
from .fake_daytona import FakeDaytona
from .fake_neo4j import FakeNeo4jDriver

__all__ = [
    "FakeButterbase",
    "FakeCognee",
    "FakeDaytona",
    "FakeNeo4jDriver",
    "install_all",
    "uninstall_all",
]


def install_all(
    *,
    butterbase: FakeButterbase | None = None,
    cognee: FakeCognee | None = None,
    daytona: FakeDaytona | None = None,
    neo4j: FakeNeo4jDriver | None = None,
) -> dict[str, object]:
    """Inject fakes for every sponsor. Returns the installed instances so a caller
    (test or local runner) can assert against their captured state afterwards."""
    bb = butterbase or FakeButterbase()
    cg = cognee or FakeCognee()
    dy = daytona or FakeDaytona()
    n4 = neo4j or FakeNeo4jDriver()

    providers.set_provider("butterbase", bb)
    providers.set_provider("cognee", cg)
    providers.set_provider("daytona", dy)
    providers.set_provider("neo4j_driver", n4)

    return {"butterbase": bb, "cognee": cg, "daytona": dy, "neo4j": n4}


def uninstall_all() -> None:
    providers.reset_providers()
