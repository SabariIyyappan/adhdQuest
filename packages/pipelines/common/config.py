"""Central configuration for the RocketRide pipelines (Person B).

Loads from environment (see repo `.env.example`). Import `settings` everywhere
rather than reading os.environ directly, so config has one home.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Butterbase
    butterbase_url: str = os.getenv("BUTTERBASE_URL", "")
    butterbase_service_key: str = os.getenv("BUTTERBASE_SERVICE_KEY", "")
    ai_gateway_url: str = os.getenv("BUTTERBASE_AI_GATEWAY_URL", "")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")

    # Daytona
    daytona_api_key: str = os.getenv("DAYTONA_API_KEY", "")
    daytona_api_url: str = os.getenv("DAYTONA_API_URL", "")
    daytona_snapshot: str = os.getenv("DAYTONA_SNAPSHOT", "adhdquest-pygame-base")
    game_preview_port: int = int(os.getenv("GAME_PREVIEW_PORT", "5000"))

    # Model tiers (routed via the Butterbase AI gateway)
    model_fast: str = os.getenv("AI_MODEL_FAST", "claude-haiku-4-5-20251001")
    model_strong: str = os.getenv("AI_MODEL_STRONG", "claude-sonnet-5")


settings = Settings()
