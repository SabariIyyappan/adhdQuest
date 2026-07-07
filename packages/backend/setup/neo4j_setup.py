"""Provision the ADHDQuest Neo4j graph (Person A, Day-1 priority).

Runs, in dependency order:
  1. schema.cypher            — constraints + indexes
  2. seed_curriculum.cypher   — the grades 3–6 prerequisite graph (ALL pipelines depend on it)
  3. gds_projections.cypher   — in-memory GDS graphs the queries read
  4. seed_demo_child.cypher   — optional demo history (--with-demo)

Usage:
    python -m backend.setup.neo4j_setup                 # schema + curriculum + projections
    python -m backend.setup.neo4j_setup --with-demo     # + demo child history
    python -m backend.setup.neo4j_setup --projections-only   # after a Neo4j restart

Reads NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD from the environment (or a .env file
at the repo root). Requires the Neo4j Graph Data Science plugin to be installed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import ClientError

try:  # optional: load repo-root .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except Exception:  # pragma: no cover - dotenv is a convenience only
    pass

from .cypher_runner import run_cypher_file  # noqa: E402

_NEO4J_DIR = Path(__file__).resolve().parents[1] / "neo4j"

SCHEMA = _NEO4J_DIR / "schema.cypher"
CURRICULUM = _NEO4J_DIR / "seed_curriculum.cypher"
PROJECTIONS = _NEO4J_DIR / "gds_projections.cypher"
DEMO = _NEO4J_DIR / "seed_demo_child.cypher"


def _driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        sys.exit("NEO4J_PASSWORD is not set. Copy .env.example to .env and fill it in.")
    return GraphDatabase.driver(uri, auth=(user, password))


def _assert_gds(driver) -> None:
    """Fail fast with a clear message if the GDS plugin is missing."""
    try:
        with driver.session() as s:
            version = s.run("RETURN gds.version() AS v").single()["v"]
        print(f"  Graph Data Science plugin detected (v{version})")
    except ClientError:
        sys.exit(
            "Neo4j Graph Data Science plugin not found. Install GDS (Aura DS, or add the\n"
            "plugin to a self-hosted instance) — every replan/report query depends on gds.*"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision the ADHDQuest Neo4j graph.")
    parser.add_argument("--with-demo", action="store_true", help="also seed the demo child history")
    parser.add_argument(
        "--projections-only",
        action="store_true",
        help="only (re)build GDS in-memory graphs — run this after a Neo4j restart",
    )
    args = parser.parse_args()

    driver = _driver()
    try:
        driver.verify_connectivity()
        print(f"Connected to Neo4j at {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
        _assert_gds(driver)

        if args.projections_only:
            _run("GDS projections", driver, PROJECTIONS)
            print("Done (projections only).")
            return

        _run("Schema (constraints + indexes)", driver, SCHEMA)
        _run("Curriculum prerequisite graph", driver, CURRICULUM)
        _run("GDS projections", driver, PROJECTIONS)
        if args.with_demo:
            _run("Demo child history", driver, DEMO)

        print("\nNeo4j provisioning complete.")
        if not args.with_demo:
            print("Tip: re-run with --with-demo before the demo to seed prior sessions.")
    finally:
        driver.close()


def _run(label: str, driver, path: Path) -> None:
    n = run_cypher_file(driver, path)
    print(f"  {label}: {n} statement(s) from {path.name}")


if __name__ == "__main__":
    main()
