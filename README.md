# ADHDQuest

An agentic learning companion for ADHD children (ages 8–13). A parent uploads a PDF
homework assignment; the system extracts every question, generates a personalized
multi-level Python mini-game in a secure sandbox, detects struggle in real time and
replans, remembers the child across sessions, and produces insight reports for parents
and doctors.

See [ADHDQuest_Implementation_Plan.md](./ADHDQuest_Implementation_Plan.md) for the full design.

## Monorepo layout

```
packages/
  contracts/    Shared cross-boundary data shapes (Section 8 of the plan).
                Single source of truth for every JSON contract. TS + JSON Schema.

  backend/      Person A — Butterbase infra, Neo4j, Cognee.
    schema/       Postgres declarative schema + RLS policies.
    functions/    Deno serverless functions (YouTube lookup, Cognee Q&A).
    actors/       Durable actor session-state + trigger logic.
    neo4j/        Graph schema, curriculum seed, GDS/Cypher queries.
    cognee/       Cognee client wrappers (recall / remember / cognify / memify).

  pipelines/    Person B — RocketRide pipelines + Daytona.
    pipeline1_ingestion/        PDF -> game.
    pipeline2_replan/           Struggle -> replan.
    pipeline3_memory_report/    Session end -> memory + report.
    nodes/                      Reusable custom nodes (Cognee, Daytona, Neo4j).
    daytona/                    Game template library + snapshot prep.

  frontend/     Person C — React SPA (parent flow + doctor dashboard).
```

## Sponsor → package map

| Sponsor      | Lives in                                   |
|--------------|--------------------------------------------|
| Butterbase   | `packages/backend`                         |
| RocketRide   | `packages/pipelines`                       |
| Neo4j        | `packages/backend/neo4j`                   |
| Cognee       | `packages/backend/cognee`, pipeline nodes  |
| Daytona      | `packages/pipelines/daytona`               |

## Getting started

1. `cp .env.example .env` and fill in credentials.
2. Backend: see [packages/backend/README.md](./packages/backend/README.md).
3. Pipelines: see [packages/pipelines/README.md](./packages/pipelines/README.md).
4. Frontend: see [packages/frontend/README.md](./packages/frontend/README.md).

## Contract ownership

Nobody edits a shared contract in `packages/contracts` unilaterally — those shapes cross
person boundaries. See that package's README before changing anything there.
