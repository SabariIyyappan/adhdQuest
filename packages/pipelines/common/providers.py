"""Dependency-injection seam for sponsor clients (Person B).

Every sponsor integration (Butterbase, Daytona, Cognee, Neo4j) is reached through
one of the ``get_*`` accessors here instead of a module-level client. Two reasons:

1. **Import safety.** The real SDKs (``daytona_sdk``, ``cognee``, ``neo4j``,
   ``rocketride``) are heavy and may be absent in a local dev checkout. Importing
   them lazily inside the factory means ``import pipelines...`` never fails just
   because a sponsor SDK isn't installed yet.

2. **Local-first + testability.** Person A's services are mocked while we build
   locally (see ``pipelines.mocks``). A test or the local runner calls
   :func:`set_provider` to inject an in-memory fake; production leaves the
   overrides empty and the real SDK-backed factory runs.

Usage::

    from ..common import providers
    bb = providers.get_butterbase()          # real or injected fake

    # in tests / local runner:
    providers.set_provider("butterbase", FakeButterbase())
    ...
    providers.reset_providers()
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

# --- override registry ------------------------------------------------

_overrides: dict[str, Any] = {}


def set_provider(name: str, obj: Any) -> None:
    """Inject a client (typically a mock). Overrides win over the real factory
    and over any lru_cache'd real client."""
    _overrides[name] = obj


def reset_providers() -> None:
    """Clear all injected clients. Call in test teardown / after a local run."""
    _overrides.clear()


def _resolve(name: str, factory: Callable[[], Any]) -> Any:
    if name in _overrides:
        return _overrides[name]
    return factory()


# --- Butterbase (Person A REST + realtime + KV + serverless) ----------


@lru_cache(maxsize=1)
def _real_butterbase() -> Any:
    from .butterbase import Butterbase

    return Butterbase()


def get_butterbase() -> Any:
    return _resolve("butterbase", _real_butterbase)


# --- Daytona (sandbox lifecycle) --------------------------------------


@lru_cache(maxsize=1)
def _real_daytona() -> Any:
    from daytona_sdk import Daytona  # type: ignore

    from .config import settings

    return Daytona(api_key=settings.daytona_api_key, api_url=settings.daytona_api_url)


def get_daytona() -> Any:
    return _resolve("daytona", _real_daytona)


# --- Cognee (child memory) --------------------------------------------


@lru_cache(maxsize=1)
def _real_cognee() -> Any:
    # The backend package owns the Neo4j-backed dataset conventions.
    from backend.cognee import client as cognee_client

    return cognee_client


def get_cognee() -> Any:
    return _resolve("cognee", _real_cognee)


# --- Neo4j (GDS driver) -----------------------------------------------


@lru_cache(maxsize=1)
def _real_neo4j_driver() -> Any:
    from neo4j import GraphDatabase

    from .config import settings

    return GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def get_neo4j_driver() -> Any:
    return _resolve("neo4j_driver", _real_neo4j_driver)
