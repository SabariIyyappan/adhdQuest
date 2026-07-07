# pipelines — Person B (RocketRide · Daytona)

The processing spine. Every transformation between sponsors passes through a
RocketRide pipeline node. Three pipelines, plus reusable custom nodes, the Daytona
game runtime, and an in-memory mock layer so the whole spine runs **locally with no
live sponsors** while Person A's backend is still being built.

## Layout

```
common/                     Shared clients + config.
  config.py                   Env-backed settings (Settings.*).
  butterbase.py               Butterbase REST + KV + realtime + serverless client.
  ai_gateway.py               LLM routing via Butterbase; deterministic offline fallback.
  providers.py                DI seam — lazy, injectable sponsor clients (import-safe).
nodes/                      Reusable RocketRide custom nodes:
  ocr_node.py                 PDF/text -> raw text
  ner_node.py                 text -> tagged questions (topic + difficulty 1-5)
  cognee_nodes.py             recall / ingest wrappers
  neo4j_gds_node.py           dijkstra / centrality / pagerank
  daytona_node.py             sandbox create / write / validate / critic / rewrite / stop
  youtube_node.py             calls the Butterbase youtube-lookup function
pipeline1_ingestion/        PDF upload -> personalized game.
pipeline2_replan/           3 fails -> replan + video + hot-reload.
pipeline3_memory_report/    session end -> Cognee ingest + GDS + report.
mocks/                      In-memory fakes of Butterbase / Cognee / Neo4j / Daytona.
pipes/                      RocketRide .pipe canvas files (one per pipeline).
daytona/                    Game template library + snapshot preparation.
fixtures/                   sample_worksheet.txt for local runs.
run_local.py                End-to-end local driver (Pipeline 1 -> 2 -> 3, mocked).
check.py                    Setup/wiring check (imports, .pipe validity, e2e).
```

Each `pipelineN_*/pipeline.py` wires the node sequence and is registered on the
RocketRide canvas; the heavy logic lives in `nodes/` so it is unit-testable off-canvas.

## Local-first: run with zero live sponsors

Person A's services (Butterbase, Cognee, Neo4j) and Daytona are **mocked in-process**
via `mocks/`, injected through the `common/providers.py` DI seam. No network, no SDKs.

```
python -m venv .venv && . .venv/Scripts/activate      # Windows (Git Bash)
pip install -r requirements-dev.txt                   # mock-only deps

python -m pipelines.check          # verify imports + .pipe files + e2e (run from packages/)
python -m pipelines.run_local      # full three-pipeline loop, narrated
python -m pipelines.run_local --warm   # child Cognee already knows (front-loads fractions)
pytest                             # 60+ unit + stress tests
```

> Run `check`, `run_local`, and `pytest` from the **`packages/`** directory (or with
> `packages/` on `PYTHONPATH`) so `import pipelines` resolves. `pytest` is configured
> via `pyproject.toml` (`pythonpath = [".."]`).

## Going live (RocketRide Cloud + real sponsors)

1. Install the real SDKs: `pip install -r requirements.txt`.
2. Fill `env.example` -> `.env` with the credentials Person A hands off
   (Butterbase URL/key + AI gateway, Neo4j, Daytona). See repo root `.env.example`.
3. Open the `pipes/*.pipe` files in the RocketRide VS Code extension; it manages
   `ROCKETRIDE_URI` / `ROCKETRIDE_APIKEY` in `.env` automatically.
4. Leave the providers overrides empty — the real SDK-backed factories in
   `providers.py` take over automatically (no code change).
5. Build the Daytona `adhdquest-pygame-base` snapshot (see `daytona/README.md`).

## Contracts (handoff to Person C)

The pipelines implement Section 8 of the plan; TypeScript sources of truth live in
`packages/contracts`:

| Contract | Where produced | Shape |
|----------|----------------|-------|
| B — Pipeline 1 result | `pipeline1_ingestion/output.py` | `Pipeline1Result` |
| C — realtime events | each `output.py` (`publish`) | `SessionChannelEvent` |
| D — session events | consumed by `pipeline3.../assemble.py` | `SessionEvent` |
| E — report JSON | `pipeline3_memory_report/report.py` | `SessionReport` |

Webhook URLs and the game-URL format are the remaining deliverables to Person C —
see the plan §7.
