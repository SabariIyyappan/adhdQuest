"""Configure Cognee to use the shared Neo4j graph backend + LanceDB vector store.

Cognee reads most settings from environment variables, and also exposes setters on
``cognee.config``. We do both (env first, then defensive setter calls) so a single
``configure_cognee()`` works across SDK versions. Import side-effect free: callers
invoke :func:`configure_cognee` once at process start (the client does this lazily).

Env consumed (see repo .env.example):
    NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
    GRAPH_DATABASE_PROVIDER (default neo4j)
    VECTOR_DB_PROVIDER      (default lancedb)
    BUTTERBASE_AI_GATEWAY_URL + AI_MODEL_* — Cognee's LLM routed through the gateway
    LLM_API_KEY             — key the gateway expects
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

_configured = False


def configure_cognee() -> None:
    """Idempotently point Cognee at Neo4j + LanceDB and the Butterbase AI gateway."""
    global _configured
    if _configured:
        return

    graph_provider = os.getenv("GRAPH_DATABASE_PROVIDER", "neo4j")
    vector_provider = os.getenv("VECTOR_DB_PROVIDER", "lancedb")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")

    # Cognee expects a host:port form for the graph DB URL (scheme carried separately).
    parsed = urlparse(neo4j_uri)
    graph_host = parsed.netloc or parsed.path

    env_defaults = {
        "GRAPH_DATABASE_PROVIDER": graph_provider,
        "GRAPH_DATABASE_URL": graph_host,
        "GRAPH_DATABASE_USERNAME": neo4j_user,
        "GRAPH_DATABASE_PASSWORD": neo4j_password,
        "VECTOR_DB_PROVIDER": vector_provider,
    }
    for key, value in env_defaults.items():
        os.environ.setdefault(key, value)

    # Route Cognee's own LLM calls through the Butterbase AI gateway when configured.
    gateway = os.getenv("BUTTERBASE_AI_GATEWAY_URL")
    if gateway:
        os.environ.setdefault("LLM_PROVIDER", "custom")
        os.environ.setdefault("LLM_ENDPOINT", gateway)
        os.environ.setdefault("LLM_MODEL", os.getenv("AI_MODEL_STRONG", "claude-sonnet-5"))

    _apply_setters(
        graph_provider=graph_provider,
        graph_host=graph_host,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        vector_provider=vector_provider,
    )
    _configured = True


def _apply_setters(**kw: str) -> None:
    """Best-effort programmatic config for SDK versions that prefer setters.

    Guarded per-call so a renamed/absent setter never breaks startup — the env vars
    above are the authoritative path.
    """
    try:
        import cognee
    except Exception:  # pragma: no cover - cognee only present in the pipeline env
        return

    config = getattr(cognee, "config", None)
    if config is None:
        return

    _safe(config, "set_graph_database_provider", kw["graph_provider"])
    _safe(config, "set_vector_db_provider", kw["vector_provider"])
    _safe(
        config,
        "set_graph_db_config",
        {
            "graph_database_provider": kw["graph_provider"],
            "graph_database_url": kw["graph_host"],
            "graph_database_username": kw["neo4j_user"],
            "graph_database_password": kw["neo4j_password"],
        },
    )


def _safe(obj: object, method: str, *args: object) -> None:
    fn = getattr(obj, method, None)
    if callable(fn):
        try:
            fn(*args)
        except Exception:  # pragma: no cover - tolerate SDK signature drift
            pass
