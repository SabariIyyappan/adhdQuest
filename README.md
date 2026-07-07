<div align="center">

# 🎮 ADHDQuest

### *Gamified Learning for ADHD Children — Powered by a Full Agentic Stack*

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-belief--os.butterbase.dev-6C63FF?style=for-the-badge)](https://belief-os.butterbase.dev)
[![Butterbase](https://img.shields.io/badge/Deployed_on-Butterbase-FF6B6B?style=for-the-badge)](https://butterbase.ai)
[![RocketRide](https://img.shields.io/badge/Pipelines-RocketRide-00C9A7?style=for-the-badge)](https://rocketride.ai)
[![Daytona](https://img.shields.io/badge/Sandbox-Daytona-4ECDC4?style=for-the-badge)](https://daytona.io)

> **ADHDQuest turns a PDF homework assignment into a personalized, playable mini-game — in real time — using a 5-sponsor agentic pipeline that learns, adapts, and reports.**

</div>

---

## 🧠 What Is ADHDQuest?

Children with ADHD face a fundamental mismatch: homework is designed for focused, linear attention. ADHDQuest breaks that contract.

1. **A parent uploads a PDF** homework assignment
2. The system **extracts every question**, classifies it by topic and difficulty, and scores the cognitive load
3. A **multi-level Python mini-game** is generated inside a secure cloud sandbox — each level is a gamified version of a real homework question, ordered by difficulty and personalized to the child's known attention patterns
4. The game **detects struggle in real time** — 3 failures on one level triggers an automatic replan, a graph-powered prerequisite path, and a YouTube micro-lesson matched to the child's remaining attention window
5. A **cross-session memory graph** remembers every child individually, so the system gets smarter about *this specific child* over time without any re-input
6. **Structured insight reports** are generated after each session for parents and doctors, with attention arcs, concept bottleneck rankings, and medication correlation data

---

## 👥 Who Uses It

| Role | What They Do | What They See |
|------|-------------|----------------|
| 👩 **Parent** | Uploads PDF, optionally logs medication time | Upload screen → live game frame → post-session report |
| 🧒 **Child** | Plays the game | A game — never a worksheet |
| 👨‍⚕️ **Doctor / Therapist** | Reviews longitudinal behavioral data | Dashboard with weekly/monthly insight graphs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (React + Vite + TypeScript)                          │
│  Parent Upload · Game Frame · Parent Dashboard · Doctor View    │
└──────────────────────┬──────────────────────────────────────────┘
                       │  REST + WebSocket (Butterbase Realtime)
┌──────────────────────▼──────────────────────────────────────────┐
│  BUTTERBASE  — Backend-as-a-Service                             │
│  Auth · Postgres · File Storage · KV · Realtime · Serverless   │
│  AI Gateway (openai/gpt-4o) · RAG · Durable Actors             │
└──────┬──────────────┬──────────────────┬───────────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐ ┌────────────┐  ┌────────────────────────────────┐
│ ROCKETRIDE │ │   NEO4J    │  │  COGNEE                        │
│ 3 Pipelines│ │ Graph DB   │  │  Memory Layer (→ Neo4j)        │
│ (agentic)  │ │ GDS Algos  │  │  remember · cognify · memify   │
└─────┬──────┘ └────────────┘  └────────────────────────────────┘
      │
      ▼
┌─────────────┐
│  DAYTONA    │
│  Sandbox    │
│  Secure     │
│  Game Runs  │
└─────────────┘
```

---

## 🧰 Sponsor Tools & Why Each One Is Essential

### 🟣 Butterbase — The Backend Brain

> *If Butterbase disappears, there is no auth, no data, no real-time, no AI routing, and no YouTube lookup.*

Butterbase is the **central nervous system** of ADHDQuest. Every other sponsor routes through it.

| Feature | How ADHDQuest Uses It |
|---------|----------------------|
| **OAuth + JWT Auth** | Google/email login for parents and doctors. Role (`parent` / `doctor`) is embedded in the JWT claim — no separate user table needed. |
| **Row-Level Security (RLS)** | Child data rows are cryptographically invisible to any user who is not the parent of that child or a doctor explicitly assigned. COPPA-safe by design. |
| **Postgres + Auto-REST** | Stores all persistent state: `children`, `assignments`, `sessions`, `questions`, `session_events`, `reports`, `video_recommendations`. |
| **File Storage (S3/R2)** | PDF assignments are uploaded here. Presigned URLs are passed directly into RocketRide Pipeline 1 as the input payload. |
| **KV Store (TTL)** | Holds live session state per child: current level index, fail count, elapsed time, replan status. Auto-expires when the session times out. |
| **Durable Actors** | One stateful actor per active child session. Accumulates events without race conditions, even across concurrent game actions. |
| **Realtime (WebSocket)** | Pushes events to the browser: game URL when generated, replan events during gameplay, and "session complete" to the parent dashboard. Zero polling. |
| **Serverless Functions (Deno)** | Hosts the YouTube Data API integration. Called by Pipeline 2 with a concept tag + remaining attention seconds → returns a ranked micro-lesson. |
| **AI Gateway** | Routes all LLM calls. Fast model (`gpt-4o-mini`) for extraction/classification; strong model (`gpt-4o`) for game spec generation, replan reasoning, and report synthesis. One key, one bill. |
| **RAG** | Pre-loaded with grade-level curriculum maps (skill prerequisites) and IEP accommodation templates. The game-spec LLM queries this at generation time. |

---

### 🟢 RocketRide — The Agentic Processing Spine

> *If RocketRide disappears, there is no pipeline to turn a PDF into a game, no replan logic, and no memory ingestion.*

RocketRide hosts all three **multi-step AI workflows**. Every transformation between sponsors passes through a RocketRide pipeline.

#### Pipeline 1 — Ingestion & Game Generation *(triggered on PDF upload)*

```
Webhook (PDF URL + child_id from Butterbase)
  ↓
OCR Node          → raw text extraction (pypdf fallback)
  ↓
NER Node          → tags each question: topic, operation type, difficulty (1–5)
  ↓
LLM (fast)        → scores cognitive load, estimates attention window
  ↓
Cognee Recall     → pulls this child's known struggles, patterns, preferences
  ↓
LLM (strong)      → generates full game spec: level ordering, mechanics, checkpoints
  ↓
Daytona Agent     → creates sandbox, writes game.py, validates, critic-repairs (3x max)
                  → returns live preview URL
  ↓
Output            → writes session + game URL to Butterbase, triggers realtime push
```

#### Pipeline 2 — Struggle Replan *(triggered on 3rd level failure)*

```
Webhook (child_id, level_id, concept_tag, time_elapsed from Butterbase KV)
  ↓
Neo4j GDS         → Dijkstra shortest path on prerequisite skill graph
                  → finds ordered concepts to cover before the blocked one
  ↓
LLM (strong)      → decides strategy: prerequisite inject / reorder / confidence builder
  ↓
YouTube Lookup    → calls Butterbase serverless fn → returns micro-lesson ≤ attention window
  ↓
Daytona Agent     → reconnects to warm sandbox, hot-rewrites failing level in-place
  ↓
Output            → logs replan event to Butterbase, pushes new level + video to game frame
```

#### Pipeline 3 — Session Memory & Report *(triggered on session end)*

```
Webhook (full session JSON from Butterbase)
  ↓
Cognee Ingest     → cognee.remember() → cognee.cognify() → cognee.memify()
                  → writes entity/relationship graph to Neo4j
  ↓
Neo4j GDS         → betweenness centrality: top bottleneck concept
                  → pageRank: most impactful struggle patterns
                  → Cypher: attention trend over last N sessions
  ↓
LLM (strong)      → synthesizes insight narrative, recommendations, medication correlation
  ↓
Output            → stores role-gated report in Butterbase (parent: summary, doctor: full)
```

---

### 🔵 Daytona — The Secure Game Sandbox

> *If Daytona disappears, there is no game — only a PDF and a list of questions.*

Every game runs inside a **Daytona sandbox** — an isolated, pre-imaged cloud environment that contains the full Python + pygame/turtle runtime.

| Capability | ADHDQuest Usage |
|-----------|----------------|
| **Snapshot (pre-built image)** | `adhdquest-pygame-base:1.0` — Python, pygame, turtle, all dependencies pre-installed. Sandbox creation takes ~2s instead of minutes. |
| **`sandbox.create()`** | Pipeline 1 spins up a fresh sandbox per session, pre-loaded from the snapshot. |
| **`sandbox.fs` write** | The game-builder agent writes `game.py` directly into the sandbox filesystem. |
| **`sandbox.process.code_run()`** | Validates the generated game actually executes without errors. On failure, a critic agent rewrites and re-runs (up to 3 iterations). |
| **`sandbox.getPreviewLink(port=5000)`** | Returns the live, publicly accessible game URL that gets pushed to the parent's browser. |
| **Reconnect by ID (Pipeline 2)** | The sandbox ID is persisted in Butterbase KV. When a replan triggers, Pipeline 2 reconnects to the *same warm sandbox* and hot-rewrites only the failing level. |
| **`sandbox.stop()` (Pipeline 3)** | Cleanly stops the sandbox at session end to preserve state for potential resumption. |

---

### 🟡 Cognee — The Self-Improving Memory Layer

> *If Cognee disappears, every session starts from zero. The system has no knowledge of the child.*

Cognee is the **long-term memory** of ADHDQuest. It converts raw session events into a structured knowledge graph stored in Neo4j, then uses that graph to personalize every future session.

| Method | ADHDQuest Usage |
|--------|----------------|
| **`cognee.remember()`** | Ingests structured session JSON (events, levels, fails, replans, attention arc). |
| **`cognee.cognify()`** | Runs the ECL (Extract-Classify-Link) pipeline: extracts entities (topic nodes, struggle edges, timing edges), embeds them, and commits to Neo4j. |
| **`cognee.memify()`** | Prunes stale nodes, strengthens recurring edges, and adds derived facts (e.g. `"attention < 12min on fractions across 4 sessions"`). |
| **`cognee.recall()`** | Called at the start of Pipeline 1. Returns a structured summary of known struggle topics, attention window estimate, preferred explanation style, and last session summary — personalized to *this child*. |

---

### 🔴 Neo4j + GDS — The Graph Intelligence Layer

> *If Neo4j disappears, there are no prerequisite paths, no bottleneck analysis, and no longitudinal pattern detection.*

Neo4j stores the **curriculum knowledge graph** and the **child behavioral graph** built by Cognee. The Graph Data Science (GDS) library runs analytics across both.

| Algorithm | Pipeline | Purpose |
|-----------|----------|---------|
| **Dijkstra Shortest Path** | Pipeline 2 | Finds the shortest prerequisite path from a mastered concept to the blocked one, telling the replan agent exactly what to cover first. |
| **Betweenness Centrality** | Pipeline 3 | Identifies the single concept node most responsible for blocking progress across all sessions — the #1 bottleneck. |
| **PageRank** | Pipeline 3 | Scores struggle patterns by impact: which failures have the highest cascading effect on downstream learning. |
| **Custom Cypher Queries** | Pipeline 3 | Computes attention arc trends over the last N sessions, surfaced in the doctor report. |

---

## 📦 Monorepo Structure

```
adhdQuest/
├── packages/
│   ├── frontend/                 # React + Vite + TypeScript SPA
│   │   ├── src/routes/           # LoginPage, ParentDashboard, DoctorDashboard, GameFrame
│   │   ├── src/hooks/            # useSession, useChildReports, useRealtime
│   │   └── src/components/       # StatCard, Charts, ReplanOverlay, ...
│   │
│   ├── backend/                  # FastAPI backend (Butterbase proxy + auth validation)
│   │   └── tests/                # 10 passing tests
│   │
│   ├── pipelines/                # RocketRide pipeline logic (Python)
│   │   ├── nodes/                # ocr_node, ner_node, cognee_nodes, daytona_node,
│   │   │                         # neo4j_gds_node, youtube_node
│   │   ├── pipes/                # pipeline1_ingestion.pipe
│   │   │                         # pipeline2_replan.pipe
│   │   │                         # pipeline3_memory_report.pipe
│   │   ├── common/               # providers.py (DI seam for Daytona, Cognee, Neo4j)
│   │   ├── mocks/                # Full mock stack for local development
│   │   ├── run_local.py          # End-to-end local test runner (no cloud needed)
│   │   └── tests/                # 64 passing tests
│   │
│   └── contracts/                # Shared TypeScript types (Contract A–E)
│
├── .rocketride/                  # RocketRide extension config + 124 component schemas
├── .env.example                  # All required environment variables documented
└── ADHDQuest_Implementation_Plan.md   # Full architecture spec
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and `pnpm`
- Python 3.11+
- A Butterbase account (for backend + deployment)
- A RocketRide account (for pipeline orchestration)
- A Daytona account (for sandboxed game execution)
- A Neo4j AuraDB instance
- A Cognee API key
- A Google Gemini API key (free tier sufficient)

### Environment Setup

```bash
# Clone the repo
git clone https://github.com/your-org/adhdQuest
cd adhdQuest

# Copy and fill in all environment variables
cp .env.example .env
```

Key environment variables:

| Variable | Description |
|----------|-------------|
| `BUTTERBASE_URL` | Butterbase app API endpoint |
| `BUTTERBASE_ANON_KEY` | Public anon key (used in frontend) |
| `BUTTERBASE_SERVICE_KEY` | Service key (used in backend) |
| `ROCKETRIDE_APIKEY` | RocketRide API key |
| `ROCKETRIDE_URI` | `https://api.rocketride.ai` |
| `DAYTONA_API_KEY` | Daytona cloud API key |
| `NEO4J_URI` | Neo4j AuraDB connection URI |
| `NEO4J_PASSWORD` | Neo4j password |
| `ROCKETRIDE_GEMINI_KEY` | Google Gemini API key (free tier) |

### Run Locally

```bash
# Install frontend dependencies
pnpm install

# Start the frontend dev server
pnpm --filter @adhdquest/frontend run dev

# Run the full pipeline locally (with mocks — no cloud accounts needed)
cd packages/pipelines
PYTHONPATH=. python3 run_local.py

# Run all tests
PYTHONPATH=.:.. python3 -m pytest tests          # backend (10 tests)
PYTHONPATH=.:.. python3 -m pytest               # pipelines (64 tests)
```

### Deploy to Butterbase

```bash
# Build the frontend
pnpm --filter @adhdquest/frontend run build

# Deploy via the Butterbase MCP (or CLI)
# Your live URL: https://<app-name>.butterbase.dev
```

---

## 🧪 Test Coverage

| Package | Tests | Status |
|---------|-------|--------|
| `packages/backend` | 10 | ✅ All passing |
| `packages/pipelines` | 64 | ✅ All passing |
| `packages/pipelines/check.py` | 12 hard checks | ✅ All passing |

All pipeline logic runs with a full **mock stack** locally — no cloud credentials required for development or CI.

---

## 📊 Data Contracts

All inter-service data shapes are versioned in `packages/contracts/`:

| Contract | Direction | Description |
|----------|-----------|-------------|
| **Contract A** | Frontend → Pipeline 1 | PDF upload payload: `child_id`, `assignment_id`, `pdf_storage_url`, `child_profile` |
| **Contract B** | Pipeline 1 → Frontend | Game ready: `session_id`, `game_url`, `level_map`, `attention_estimate` |
| **Contract C** | Any Pipeline → Frontend | Realtime event: `game_ready` / `replan` / `session_end` |
| **Contract D** | Frontend → Pipeline 2 | Struggle trigger: `child_id`, `session_id`, `level_index`, `concept_tag`, `time_elapsed` |
| **Contract E** | Pipeline 3 → Frontend | Session report: `parent_summary`, `doctor_narrative`, `concept_bottlenecks`, `attention_arc` |

---

## 🏆 Hackathon Submission

ADHDQuest was built for **[Hackathon Name]** using all 5 required sponsor integrations:

| Sponsor | Integration Depth |
|---------|------------------|
| ✅ **Butterbase** | Auth, DB, Storage, KV, Realtime, Serverless, AI Gateway, RAG, Durable Actors |
| ✅ **RocketRide** | 3 production pipelines with agentic orchestration |
| ✅ **Daytona** | Snapshotted sandboxes, game execution, live preview URLs |
| ✅ **Cognee** | Cross-session memory graph (remember → cognify → memify → recall) |
| ✅ **Neo4j** | Prerequisite path finding, bottleneck analysis, attention trend queries |

> **The system breaks without every single sponsor.** Each owns a layer no other can replace.

---

<div align="center">

**Built with ❤️ for kids who learn differently**

[🚀 Live Demo](https://belief-os.butterbase.dev) · [📋 Implementation Plan](./ADHDQuest_Implementation_Plan.md) · [🐛 Report Issues](https://github.com/your-org/adhdQuest/issues)

</div>
