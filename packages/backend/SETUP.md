# Person A — Backend Setup Runbook

Everything Person A must provision, in Day-1 dependency order. Complete each section
top-to-bottom; later sections assume earlier ones are done.

---

## 0. API keys & accounts checklist

Fill these into the repo-root `.env` (`cp .env.example .env`). Grab each from the
source listed.

| Env var | Where to get it | Notes |
|---|---|---|
| `BUTTERBASE_URL` | Butterbase project dashboard | REST/realtime/KV base URL |
| `BUTTERBASE_ANON_KEY` | Butterbase → API keys | client-side (also `VITE_BUTTERBASE_ANON_KEY`) |
| `BUTTERBASE_SERVICE_KEY` | Butterbase → API keys | **secret**, server-side only |
| `BUTTERBASE_AI_GATEWAY_URL` | Butterbase → AI Gateway | LLM routing endpoint |
| `AI_MODEL_FAST` / `AI_MODEL_STRONG` | pick models | defaults: Claude Haiku / Sonnet |
| `NEO4J_URI` | Neo4j Aura DS or self-host | `neo4j+s://…` (Aura) or `bolt://…` |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j instance | GDS plugin **required** |
| `COGNEE_API_URL` | your Cognee deployment | cloud or self-hosted |
| `GRAPH_DATABASE_PROVIDER` | fixed = `neo4j` | ties Cognee to the same Neo4j |
| `VECTOR_DB_PROVIDER` | fixed = `lancedb` | |
| `LLM_API_KEY` | LLM provider (via gateway) | Cognee's own extraction LLM |
| `YOUTUBE_API_KEY` | Google Cloud → YouTube Data API v3 | free tier 100 units/day |
| Google OAuth Client ID + Secret | Google Cloud → OAuth consent + credentials | entered in Butterbase, not `.env` |

Hand-off values you must give Person B/C are listed at the bottom.

---

## 1. Butterbase (auth · Postgres · storage · KV · realtime · functions · AI gateway)

1. **Create the app** in Butterbase; copy the URL + anon/service keys into `.env`.
2. **Schema:** apply `schema/tables.sql` then `schema/rls.sql` through the Butterbase
   declarative-schema/SQL endpoint. Person A owns migrations — nobody else edits schema.
3. **OAuth:** enable Google login. In Google Cloud create OAuth credentials, add the
   Butterbase callback URL, then paste Client ID + Secret into Butterbase auth settings.
   Store `role` (`parent` | `doctor`) as a JWT claim — RLS reads it.
4. **Storage bucket** for PDFs: content-type restricted to `application/pdf`, a sane max
   size (e.g. 10 MB), and CORS allowing the frontend origin. The frontend uploads to
   `assignments/{child_id}/{uuid}.pdf` (see `frontend/src/lib/butterbase.ts`).
5. **KV store** with the keys/TTLs in `config/kv_keys.ts`:
   `session:{child_id}:active` (TTL 2h) and `child:{child_id}:cognee_dataset` (no TTL).
6. **Realtime channel** `child:{child_id}:session` carrying Contract C events
   (`game_ready`, `replan`, `session_end`).
7. **Serverless functions:** deploy both Deno functions — see `functions/README.md`.
8. **AI gateway:** configure model routing so the pipelines can address tasks by tier —
   fast tier → extraction/classification, strong tier → generation/synthesis
   (`config/ai_gateway.ts` is the source of truth for the mapping).
9. **RAG:** create a collection and ingest the grade 3–6 math prerequisite/curriculum
   docs + IEP accommodation templates; the game-spec LLM node reads this at generation.
10. **Durable actors:** wire the per-session actor (`actors/session_actor.ts`) — it folds
    gameplay events, keeps the per-level fail counter, and fires the Pipeline 2 webhook at
    3 fails and the Pipeline 3 webhook on `session_end`.

---

## 2. Neo4j graph + GDS  (do this before any pipeline runs)

Requires the **Graph Data Science** plugin (Aura DS, or add the plugin to a self-host).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r packages/backend/requirements.txt

# from packages/ so `backend` is importable as a top-level package:
cd packages
python -m backend.setup.neo4j_setup --with-demo
```

This applies, in order: `schema.cypher` → `seed_curriculum.cypher` →
`gds_projections.cypher` → `seed_demo_child.cypher`. It fails fast with a clear message
if the GDS plugin is missing.

> GDS in-memory graphs are lost on a Neo4j restart. Re-materialize them with:
> `python -m backend.setup.neo4j_setup --projections-only`

Seed the prerequisite graph FIRST in real life too — Pipeline 2's replan is a random
guess without it (plan §10).

---

## 3. Cognee (Neo4j-backed memory + LanceDB vectors)

`cognee/config.py` points Cognee at the same Neo4j (`GRAPH_DATABASE_PROVIDER=neo4j`) and
LanceDB, and routes Cognee's own LLM through the Butterbase AI gateway. It runs
automatically the first time any `cognee/client.py` function is called.

Smoke test once `.env` is populated and the Cognee service is up:

```bash
cd packages
python -c "import asyncio; from backend.cognee import client; \
print(asyncio.run(client.recall('00000000-0000-0000-0000-0000000000d1')))"
```

A cold-start child returns the well-formed empty context; the demo child returns parsed
struggle topics / attention window.

---

## 4. Verify

```bash
cd packages/pipelines && python -m pytest        # ordering + contract tests
cd packages/backend  && python -m pytest tests   # cypher runner + recall parsing
cd packages/backend/functions && deno task check # function typecheck (needs deno)
```

---

## Deliverables to hand to Person B / C

- **Person B:** `BUTTERBASE_URL` (REST base), service key, KV read/write key layout
  (`config/kv_keys.ts`), realtime channel spec (Contract C), AI-gateway URL + tier map
  (`config/ai_gateway.ts`), `NEO4J_URI`/user/password, `COGNEE_API_URL`, and the Cognee
  dataset naming convention (`child_{child_id}`).
- **Person C:** `VITE_BUTTERBASE_URL`, `VITE_BUTTERBASE_ANON_KEY`, the realtime channel
  name (`child:{child_id}:session`), and the `cognee-qa` function name for the doctor
  Q&A panel.
