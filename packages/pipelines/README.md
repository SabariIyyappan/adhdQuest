# pipelines — Person B (RocketRide · Daytona)

The processing spine. Every transformation between sponsors passes through a
RocketRide pipeline node. Three pipelines, plus reusable custom nodes and the
Daytona game runtime.

## Layout

```
common/                     Shared clients + config (Butterbase REST, env).
nodes/                      Reusable RocketRide custom nodes:
  ocr_node.py                 PDF -> raw text
  ner_node.py                 text -> tagged questions
  cognee_nodes.py             recall / ingest wrappers
  neo4j_gds_node.py           dijkstra / centrality / pagerank
  daytona_node.py             sandbox create / write / validate / rewrite
  youtube_node.py             calls the Butterbase youtube-lookup function
pipeline1_ingestion/        PDF upload -> personalized game.
pipeline2_replan/           3 fails -> replan + video + hot-reload.
pipeline3_memory_report/    session end -> Cognee ingest + GDS + report.
daytona/                    Game template library + snapshot preparation.
```

Each `pipelineN_*/pipeline.py` wires the node sequence and is registered on the
RocketRide canvas; the heavy logic lives in `nodes/` so it is unit-testable off-canvas.

## Run locally

```
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements.txt
pytest                                              # node unit tests
```

Webhook URLs, the game-URL format, session-event spec, and report schema are the
deliverables handed to Person C — see the plan §7.
