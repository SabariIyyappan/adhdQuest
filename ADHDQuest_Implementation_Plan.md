# ADHDQuest — Implementation Plan

> **No code. Logic, architecture, data flows, and team responsibilities only.**

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [System Architecture](#2-system-architecture)
3. [Sponsor Integration Map](#3-sponsor-integration-map)
4. [Data Models](#4-data-models)
5. [The Three Pipelines](#5-the-three-pipelines)
6. [Feature Logic](#6-feature-logic)
7. [Team Split](#7-team-split)
8. [Integration Contracts](#8-integration-contracts)
9. [Demo Script](#9-demo-script)
10. [Dependency & Risk Register](#10-dependency--risk-register)

---

## 1. Product Overview

### What It Is

ADHDQuest is an agentic learning companion for ADHD children (ages 8–13) that:

1. Accepts a **PDF homework assignment** upload from a parent
2. Extracts every question, classifies each by topic and difficulty, and scores the assignment's overall cognitive load
3. Generates a **multi-level Python mini-game** — built inside a secure isolated sandbox — where each level is a gamified version of a real homework question, ordered by difficulty and personalized to the child's known attention patterns
4. **Detects struggle in real time** (3 failures on one level triggers replanning), restructures remaining levels, and surfaces a YouTube micro-lesson matched to the exact concept and the child's remaining attention window
5. **Remembers everything** across sessions using a self-improving memory graph (Cognee + Neo4j), so the system gets smarter about this specific child without any manual re-input
6. **Generates a structured insight report** after each session, shared with parents and doctors, containing attention arc, struggle patterns, concept bottleneck ranking, and cross-session behavioral trends

### Who Uses It

| Role | What They Do | What They See |
|------|-------------|---------------|
| **Parent** | Uploads PDF, logs medication time (optional), views session report | Upload screen → live game → post-session report |
| **Child** | Plays the game | A game — never a worksheet |
| **Doctor / Therapist** | Reviews longitudinal data | Dashboard with weekly/monthly insight graphs |

### Core Constraint

The product **breaks without every single sponsor.** Each sponsor owns a layer no other can replace.

---

## 2. System Architecture

### High-Level Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (React SPA)                                          │
│  Parent Upload · Game Frame · Parent Dashboard · Doctor View    │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST + WebSocket (Butterbase realtime)
┌──────────────────────▼──────────────────────────────────────────┐
│  BUTTERBASE  (Backend Infrastructure)                           │
│  Auth (OAuth + RLS) · Postgres · File Storage · KV · Realtime  │
│  Serverless Functions · AI Gateway · Durable Actors             │
└──────┬──────────────┬──────────────────┬───────────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐ ┌────────────┐  ┌────────────────────────────────┐
│ ROCKETRIDE │ │   NEO4J    │  │  COGNEE                        │
│ Pipelines  │ │ Graph DB   │  │  Memory Layer (backed by Neo4j)│
│ (3 flows)  │ │ GDS Algos  │  │  cognify · memify · recall     │
└────────────┘ └────────────┘  └────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  DAYTONA    │
│  Sandbox    │
│  (game runs │
│   here)     │
└─────────────┘
```

### Request Flow Summary

```
PDF Upload
  → Butterbase stores file (S3/R2)
  → triggers RocketRide Pipeline 1 (ingestion)
    → OCR node extracts text from PDF
    → NER node tags questions by topic + difficulty
    → LLM node scores cognitive load + attention estimate
    → Cognee recall → pulls prior child memory
    → LLM node generates game spec (levels, ordering)
    → RocketRide invokes Daytona SDK
      → sandbox.create() with pygame/turtle snapshot
      → game-builder agent writes game code into sandbox
      → sandbox.process.code_run() validates it executes
      → sandbox.getPreviewLink() returns live game URL
    → game URL + session metadata written to Butterbase Postgres
    → Butterbase realtime pushes URL to parent browser

During Gameplay
  → Child events (level complete, fail, timing) POST to Butterbase
  → Butterbase durable actor holds live session state
  → On 3rd failure: triggers RocketRide Pipeline 2 (replan)
    → Neo4j GDS shortest-path query finds prerequisite path
    → Butterbase serverless function calls YouTube Data API
    → Daytona agent rewrites the failing level in-place
    → Butterbase realtime pushes replan event to game frame

Session End
  → RocketRide Pipeline 3 (memory + report)
    → Cognee.remember() ingests structured session JSON
    → Cognee.cognify() builds graph entities + relationships
    → Cognee.memify() refines edges, strengthens patterns
    → Neo4j GDS centrality runs on longitudinal graph
    → LLM report synthesis (via Butterbase AI gateway)
    → Report stored in Butterbase, shared with doctor role
```

---

## 3. Sponsor Integration Map

### Butterbase — Backend Infrastructure

**What it owns:** Authentication, data persistence, role isolation, real-time event pushing, serverless computation, and LLM routing.

| Feature Used | Purpose in ADHDQuest |
|---|---|
| **OAuth + JWT auth** | Google/email login for parent, separate login for doctor. Role stored in JWT claims. |
| **Row-Level Security (RLS)** | Child data rows are invisible to any user whose JWT role ≠ parent_of_child OR doctor_assigned_to_child. COPPA-safe by design. |
| **Postgres + auto-REST** | Stores: children, assignments, sessions, questions, events, reports, video_recommendations |
| **File Storage (S3/R2)** | PDF assignment uploads stored here. Presigned URLs passed to RocketRide pipeline as input. |
| **KV Store (TTL)** | Holds live session state per child (current level, fail count, elapsed time, replan status). TTL = session timeout. |
| **Durable Actors** | One actor per active child session. Accumulates events without race conditions across concurrent game actions. |
| **Realtime (WebSocket)** | Pushes game URL on generation, replan events during gameplay, and "session complete" signal to parent dashboard. |
| **Serverless Functions (Deno)** | YouTube Data API call: accepts concept tag + attention_seconds_remaining, returns ranked video list. Runs on-demand. |
| **AI Gateway** | Routes LLM calls: cheap/fast model (e.g. Haiku) for extraction and classification; strong model (e.g. Sonnet) for game spec generation, replan reasoning, and report synthesis. |
| **RAG** | Ingested with: grade-level curriculum maps (which skills are prerequisites for which), IEP accommodation templates. Used by LLM during game spec generation. |

**Why it breaks without Butterbase:** There is no auth layer, no role isolation (doctor reads any child's data), no realtime (parent has to poll), no serverless YouTube call, no AI gateway routing (one hardcoded expensive model for everything), and no live session state between game events.

---

### RocketRide — The Processing Spine (3 Pipelines)

**What it owns:** All multi-step AI processing logic. Every transformation between sponsors passes through a RocketRide pipeline node.

**Pipeline 1 — Ingestion & Game Generation** (triggered on PDF upload)

```
[Webhook Source Node]  ← presigned URL + child_id from Butterbase
        ↓
[OCR Node]  ← PDF → raw text (uses built-in Tika/Tesseract)
        ↓
[NER Node]  ← tags each question: topic, operation type, difficulty (1–5)
        ↓
[Chunking Node]  ← groups questions into logical clusters
        ↓
[Embedding Node]  ← embeds questions for semantic deduplication
        ↓
[LLM Node - fast model]  ← scores: total_questions, avg_difficulty,
                             estimated_attention_load, recommended_session_splits
        ↓
[Custom Node: Cognee Recall]  ← calls cognee.recall(child_id, "learning patterns")
                                 returns: known struggle topics, attention window,
                                 preferred explanation style, last session summary
        ↓
[LLM Node - strong model]  ← generates game spec JSON:
                               level ordering, question-to-level mapping,
                               game mechanic per topic, replan triggers,
                               attention checkpoint intervals
        ↓
[Custom Node: Daytona Game Builder Agent]
   ├── sandbox.create() from pre-built pygame snapshot
   ├── game-builder agent writes game.py to sandbox.fs
   ├── sandbox.process.code_run("python game.py --validate")
   ├── if error: critic agent rewrites, re-runs (max 3 iterations)
   └── sandbox.getPreviewLink(port=5000) → live game URL
        ↓
[Output Node]  ← writes to Butterbase: session record, game_url,
                  level_map (which question = which level),
                  triggers realtime push to parent
```

**Pipeline 2 — Struggle Replan** (triggered when child fails a level 3 times)

```
[Webhook Source Node]  ← child_id, current_level_id, fail_count,
                          time_elapsed, concept_tag from Butterbase KV
        ↓
[Custom Node: Neo4j GDS Query]
   ← CALL gds.shortestPath.dijkstra on prerequisite skill graph
     from child's current knowledge state to the blocked concept
     returns: ordered list of prerequisite skills to cover first
        ↓
[LLM Node - strong model]  ← decides replan strategy:
                               - inject prerequisite micro-level before current
                               - swap to simpler variant of same question
                               - restructure remaining level order
        ↓
[Custom Node: YouTube Lookup]
   ← calls Butterbase serverless function:
     input: concept_tag, remaining_attention_seconds
     function queries YouTube Data API for videos
     filtered by: duration ≤ remaining attention, child's grade, topic
     returns: top 1 video with title, thumbnail, url, duration
        ↓
[Custom Node: Daytona Live Rewrite]
   ← connects to existing sandbox by sandbox_id (from Butterbase KV)
   ← agent writes updated level code to sandbox.fs (in-place edit)
   ← sandbox.process.code_run("python reload_level.py")
        ↓
[Output Node]  ← writes replan event to Butterbase session log
                  Butterbase realtime pushes: new level code,
                  video recommendation, replan explanation to game frame
```

**Pipeline 3 — Session Memory & Report** (triggered on session end)

```
[Webhook Source Node]  ← full session JSON from Butterbase:
                          events[], levels_completed[], fails_by_level,
                          replans[], videos_watched[], total_time,
                          attention_arc (time vs error rate)
        ↓
[Custom Node: Cognee Ingest]
   ← cognee.remember(session_json, user_set=child_id)
   ← cognee.cognify()  → ECL pipeline:
       classify → extract entities (topic nodes, struggle edges,
       time_to_complete edges, replan_trigger nodes) → embed → commit to Neo4j
   ← cognee.memify()  → prune stale nodes, strengthen recurring edges,
                          add derived facts (e.g. "attention < 12min on fractions")
        ↓
[Custom Node: Neo4j GDS Analysis]
   ← gds.betweenness.centrality on concept nodes
     → identifies the #1 bottleneck concept across all sessions
   ← gds.pageRank on struggle nodes
     → identifies most-impactful struggle patterns
   ← Cypher query: attention_arc trend over last N sessions
        ↓
[LLM Node - strong model via Butterbase AI gateway]
   ← synthesizes: insight narrative, concept bottleneck ranking,
     attention trend summary, medication correlation (if logged),
     recommended next session structure
        ↓
[Output Node]  ← stores structured report in Butterbase Postgres
                  (role-gated: parent sees summary, doctor sees full data)
                  triggers Butterbase webhook to doctor notification endpoint
```

**Why it breaks without RocketRide:** There is no processing spine. Butterbase stores files but can't process them. Neo4j holds graphs but nothing populates them. Cognee has memory but nothing to ingest. Daytona has a sandbox but nothing to write the game. RocketRide is the nervous system connecting every other sponsor.

---

### Neo4j — The Relationship Brain

**What it owns:** The knowledge graph of learning, skill prerequisites, and longitudinal behavioral patterns.

**Graph Schema**

```
Nodes:
  (:Child {id, name, grade, attention_baseline_minutes})
  (:Session {id, child_id, date, total_minutes, completion_rate})
  (:Question {id, text, topic, difficulty, operation_type})
  (:Skill {id, name, subject, grade_level})
  (:StruggleEvent {id, session_id, level_id, fail_count, replan_triggered})
  (:Concept {id, name, subject})  ← higher-level grouping of Skills
  (:VideoRecommendation {id, youtube_id, concept, duration_seconds})
  (:MedicationLog {id, child_id, timestamp, medication, dose})

Relationships:
  (Child)-[:HAD_SESSION]->(Session)
  (Session)-[:CONTAINED_QUESTION]->(Question)
  (Session)-[:HAD_STRUGGLE]->(StruggleEvent)
  (StruggleEvent)-[:ON_CONCEPT]->(Concept)
  (Concept)-[:REQUIRES_UNDERSTANDING_OF]->(Concept)  ← THE PREREQUISITE GRAPH
  (Child)-[:HAS_MASTERED]->(Skill {confidence_score})
  (Child)-[:STRUGGLES_WITH]->(Concept {frequency, avg_fail_count})
  (VideoRecommendation)-[:EXPLAINS]->(Concept)
  (MedicationLog)-[:PRECEDED]->(Session {time_delta_minutes})
```

**GDS Algorithms Used**

| Algorithm | Trigger | What It Returns |
|---|---|---|
| `gds.shortestPath.dijkstra` | Pipeline 2 replan | Shortest prerequisite path from child's current knowledge to the blocked concept |
| `gds.betweenness.centrality` | Pipeline 3 report | Which concept node sits on the most paths → the #1 bottleneck across all sessions |
| `gds.pageRank` | Pipeline 3 report | Most influential struggle pattern nodes |
| `gds.nodeSimilarity` | Doctor dashboard (weekly) | Finds children with similar struggle profiles for anonymized cohort insights |
| `gds.linkPrediction.adamicAdar` | Optional future | Predicts which concept the child will struggle with next based on current graph state |

**Cognee's Relationship with Neo4j**

Cognee is configured with `GRAPH_DATABASE_PROVIDER=neo4j`. This means:
- When Cognee runs `cognify()`, entities and relationships it extracts are written **directly into the same Neo4j instance**
- Cognee-managed nodes coexist with our manually defined schema nodes
- `cognee.recall()` queries across both Cognee-generated nodes and our schema nodes via hybrid vector + graph traversal
- This unification means a single Neo4j Bloom visualization can show both the structured prerequisite graph AND the Cognee-inferred behavioral patterns

**Why it breaks without Neo4j:** Pipeline 2 replan becomes a random guess — there's no prerequisite graph to traverse. Pipeline 3 report loses all longitudinal analysis (no centrality, no trend Cypher queries). Cognee loses its graph backend and falls back to vector-only retrieval, meaning it can no longer do multi-hop reasoning like "which concept appears across the most struggle events across sessions."

---

### Cognee — The Self-Improving Child Memory

**What it owns:** Persistent, adaptive memory for each child that improves across sessions without any manual re-input.

**Memory Lifecycle Per Child**

```
Session 1 (no prior memory):
  cognee.recall(child_id) → returns nothing
  Game is generated from PDF + curriculum RAG alone
  Session ends → cognee.remember(session_1_data)
                 cognee.cognify()  → first knowledge graph for this child
                 cognee.memify()   → no pruning yet (too few edges)

Session 2:
  cognee.recall(child_id) → returns:
    - "struggled with fractions at minute 14"
    - "prefers visual analogies over abstract rules"
    - "completed division problems fastest"
  Game spec LLM uses this context to:
    - place fractions earlier (before fatigue sets in)
    - order visual-mechanic levels before text-only levels
    - use division as a "confidence booster" level mid-session
  Session ends → cognee.remember(session_2_data)
                 cognee.cognify() → adds new entities, strengthens existing edges
                 cognee.memify() → prunes one-off events, strengthens patterns
                                   "fraction struggle" edge weight increases
                                   "minute 14 = attention drop" fact strengthened

Session 5+:
  cognee.recall() returns a rich behavioral profile:
    - attention window narrowing on Tuesdays (if medication logs correlate)
    - always needs a success level after 2 hard levels
    - fractions require visual explanation + < 8-minute window
  Game spec is now as personalized as a human tutor with 5 sessions of notes
```

**Cognee API Usage**

| API Call | When | What It Does |
|---|---|---|
| `cognee.recall(child_id)` | Pipeline 1 start | Retrieves all prior behavioral patterns for this child |
| `cognee.remember(session_data, user_set=child_id)` | Pipeline 3 start | Ingests raw session JSON |
| `cognee.cognify()` | Pipeline 3 after remember | ECL pipeline: extract entities + relationships → commit to Neo4j |
| `cognee.memify()` | Pipeline 3 after cognify | Prune stale nodes, strengthen recurring patterns, add derived facts |
| `cognee.search(query, search_type="GRAPH_COMPLETION")` | Doctor dashboard | "Has this child improved on division over the last 3 sessions?" → returns cited answer |
| `cognee.forget(dataset=child_id)` | Account deletion | GDPR compliance — wipes all memory for a child |

**Why it breaks without Cognee:** Every session starts from zero. The game is generated solely from the PDF with no knowledge of this child. A child who always struggles with fractions after minute 12 gets the same level order every time. The doctor report cannot answer "what changed over time" — it can only describe individual sessions. The system becomes a one-time game generator, not a learning companion.

---

### Daytona — The Secure Game Runtime

**What it owns:** The isolated environment where LLM-generated Python game code is written, validated, run, and updated mid-session.

**Sandbox Lifecycle**

```
On Assignment Upload:
  daytona.create(
    snapshot="adhdquest-pygame-base",  ← pre-built snapshot with pygame,
                                          turtle, and pyglet pre-installed
    language="python",
    resources={cpu: 1, memory: 2, disk: 4},
    auto_stop_interval=60  ← pauses after 60 min of inactivity
  )
  → returns sandbox_id
  → sandbox_id stored in Butterbase KV (key: "session:{child_id}:sandbox_id")

Game Writing (by RocketRide agent):
  sandbox.fs.upload_file(game_spec_json, "game_spec.json")
  sandbox.fs.upload_file(game_template_py, "game.py")  ← agent fills template
  sandbox.process.code_run("python game.py --validate")
  → if exit_code != 0: agent reads stderr, rewrites game.py, re-runs
  → if exit_code == 0: sandbox.getPreviewLink(port=5000)
  → game URL returned to RocketRide output node

During Gameplay (live replan):
  → retrieve sandbox_id from Butterbase KV
  → daytona.get(sandbox_id)  ← reconnects to same sandbox
  → agent writes updated level_N.py to sandbox.fs
  → sandbox.process.exec("python reload_level.py")
  → game frame receives new level via WebSocket from game process

Session End:
  sandbox.stop()  ← pauses sandbox, preserves filesystem state
  sandbox_id kept in Butterbase KV with TTL = 7 days
  → if child returns within 7 days, same sandbox resumes instantly
  → after 7 days, sandbox auto-archives (state preserved in object storage)
```

**The Snapshot Strategy**

A pre-built Daytona snapshot named `adhdquest-pygame-base` is prepared once by the team with:
- Python 3.12
- pygame, turtle, pyglet (for different game mechanic options)
- A game template library (level scaffolding, input handlers, score tracking)
- A `reload_level.py` hot-reload script

This snapshot ensures sandbox creation takes < 90ms instead of needing package install time.

**Why it breaks without Daytona:** The LLM-generated Python game code has nowhere safe to run. Running it on the app server is a security violation (arbitrary code execution). Running it in the browser (via Pyodide) cannot handle the full pygame library. Without Daytona, the "game generated from your actual homework" feature — the product's core demo moment — cannot exist.

---

## 4. Data Models

### Butterbase Postgres Schema

**Tables and key columns** (Butterbase declarative schema format):

```
children
  id (uuid, pk)
  parent_user_id (uuid, fk → users)
  name (text)
  grade (int)
  attention_baseline_minutes (int, default 15)
  doctor_user_id (uuid, fk → users, nullable)
  created_at (timestamptz)

assignments
  id (uuid, pk)
  child_id (uuid, fk → children)
  pdf_storage_key (text)  ← S3/R2 key in Butterbase file storage
  subject (text)
  grade (int)
  total_questions (int)
  avg_difficulty (float)
  estimated_attention_load (text)  ← "light" | "moderate" | "heavy"
  created_at (timestamptz)

sessions
  id (uuid, pk)
  child_id (uuid, fk → children)
  assignment_id (uuid, fk → assignments)
  sandbox_id (text)  ← Daytona sandbox ID
  game_url (text)
  status (text)  ← "generating" | "active" | "replanning" | "complete"
  started_at (timestamptz)
  ended_at (timestamptz, nullable)

questions
  id (uuid, pk)
  assignment_id (uuid, fk → assignments)
  raw_text (text)
  topic (text)
  operation_type (text)  ← "division" | "fractions" | "word_problem" etc.
  difficulty (int, 1–5)
  level_index (int)  ← which game level this question maps to

session_events
  id (uuid, pk)
  session_id (uuid, fk → sessions)
  event_type (text)  ← "level_start" | "level_complete" | "level_fail" |
                        "replan_triggered" | "video_watched" | "session_end"
  level_index (int)
  timestamp (timestamptz)
  payload (jsonb)  ← time_elapsed, score, video_id, etc.

video_recommendations
  id (uuid, pk)
  session_id (uuid, fk → sessions)
  level_index (int)
  youtube_id (text)
  title (text)
  duration_seconds (int)
  concept_tag (text)
  watched (bool, default false)

reports
  id (uuid, pk)
  child_id (uuid, fk → children)
  session_id (uuid, fk → sessions)
  report_json (jsonb)  ← full structured report
  summary_text (text)  ← LLM-synthesized narrative
  created_at (timestamptz)

medication_logs (optional, parent-entered)
  id (uuid, pk)
  child_id (uuid, fk → children)
  logged_at (timestamptz)
  medication_name (text)
  dose_mg (float)
```

**RLS Policies**

```
children:  SELECT WHERE parent_user_id = auth.uid()
             OR doctor_user_id = auth.uid()

sessions:  SELECT WHERE child_id IN
             (SELECT id FROM children WHERE parent_user_id = auth.uid()
              OR doctor_user_id = auth.uid())

reports:   parent can SELECT summary_text + session_events
           doctor can SELECT full report_json

medication_logs: SELECT/INSERT only for parent_user_id = auth.uid()
```

### Butterbase KV Store

```
Key pattern: "session:{child_id}:active"
Value: {
  sandbox_id: string,
  current_level: int,
  fail_count_by_level: {level_index: int},
  replan_count: int,
  session_start_epoch: number,
  attention_seconds_elapsed: number
}
TTL: 2 hours (auto-expires if child abandons session)

Key pattern: "child:{child_id}:cognee_dataset"
Value: cognee dataset name for this child
TTL: none (permanent)
```

---

## 5. The Three Pipelines

### Pipeline 1 — Ingestion & Game Generation

**Trigger:** Butterbase webhook fires when PDF file upload completes (async indexer callback)

**Source Node:** Webhook, receives `{child_id, assignment_id, pdf_storage_url}`

**Node sequence and logic:**

1. **OCR Node** — Receives the presigned PDF URL from Butterbase storage. Uses built-in Tika/Tesseract to extract all text. Outputs: raw text string, page count, detected language.

2. **NER Node** — Receives raw text. Tags each sentence/block as a question or non-question. For each question, extracts: question text, math operation type (addition, subtraction, multiplication, division, fractions, decimals, word problem), estimated difficulty (1–5 based on operation complexity and number of steps). Outputs: structured list of `{question_id, text, topic, difficulty}`.

3. **LLM Node (fast model via Butterbase gateway)** — Receives the question list. Computes: total question count, average difficulty, difficulty distribution, estimated cognitive load category, recommended session split strategy (e.g. "split into 2 sessions of 10 questions"). Also computes suggested attention checkpoint interval (every N levels) based on cognitive load. Outputs: assignment metadata JSON.

4. **Cognee Recall Node (custom Python node)** — Calls `cognee.recall(child_id, query="learning patterns and attention history")`. Retrieves structured behavioral memory for this child: known struggle topics, average attention window, preferred explanation style, last session's performance, any medication correlation patterns. If first session, returns empty. Outputs: `prior_context` JSON (empty or rich).

5. **LLM Node (strong model via Butterbase gateway)** — Receives question list + assignment metadata + Cognee prior context + Butterbase RAG context (curriculum prerequisite map). Generates: game spec JSON including level ordering (difficulty-sorted, personalized by prior context), question-to-level mapping, game mechanic type per level (puzzle, quiz, maze, match), attention checkpoint positions, replan trigger configuration (`fail_threshold=3`), recommended session duration. Outputs: `game_spec.json`.

6. **Daytona Game Builder Node (custom Python node)** — The most complex node. Logic:
   - Call `daytona.create()` from the `adhdquest-pygame-base` snapshot
   - Write `game_spec.json` to `sandbox.fs`
   - Write generated `game.py` (from game spec template filled by LLM) to `sandbox.fs`
   - Call `sandbox.process.code_run("python game.py --validate")`
   - If exit code ≠ 0: read stderr, pass error + code back to internal critic agent, rewrite, retry (max 3 iterations)
   - If exit code = 0: call `sandbox.getPreviewLink(port=5000)` to get the live game URL
   - Store `sandbox_id` to Butterbase KV: `"session:{child_id}:active"`
   - Outputs: `{game_url, sandbox_id}`

7. **Output Node** — Writes to Butterbase Postgres: updates `sessions` row with `game_url`, `sandbox_id`, `status="active"`. Triggers Butterbase realtime push on channel `"child:{child_id}:session"` with payload `{event: "game_ready", game_url}`.

---

### Pipeline 2 — Struggle Replan

**Trigger:** Butterbase durable actor emits webhook when `fail_count_by_level[current_level] >= 3`

**Source Node:** Webhook, receives `{child_id, session_id, current_level_index, concept_tag, time_elapsed_seconds, attention_baseline_seconds}`

**Node sequence and logic:**

1. **Neo4j GDS Query Node (custom Python node)** — Runs a Cypher + GDS procedure:
   - First: query which skills the child has mastered (`Child-[:HAS_MASTERED]->Skill`)
   - Then: run `gds.shortestPath.dijkstra` from the blocked concept node to the nearest mastered ancestor concept, traversing `REQUIRES_UNDERSTANDING_OF` edges in reverse
   - Returns: ordered list of prerequisite concepts the child needs before re-attempting the blocked concept, ranked by how many sessions this child has engaged with each
   - Outputs: `{prerequisite_path: [{concept, sessions_exposed, mastery_confidence}]}`

2. **LLM Node (strong model)** — Receives: prerequisite path, current game spec, time elapsed, attention window. Decides replan strategy:
   - If prerequisite is 1 step away and attention remains: inject a simpler micro-level before the failing level
   - If prerequisite is 2+ steps away: restructure remaining levels to address foundation first
   - If attention window nearly exhausted: swap current level to a low-stakes confidence-builder, save the hard concept for next session
   - Outputs: `{strategy, updated_level_order, replacement_level_spec, replan_explanation}`

3. **Butterbase Serverless Function Call Node** — Calls the YouTube lookup serverless function deployed on Butterbase (Deno runtime). Passes: `concept_tag`, `remaining_attention_seconds = attention_baseline_seconds - time_elapsed_seconds`, `grade_level`. Function logic (Deno): calls YouTube Data API with `search.list`, filters by `videoDuration=short` (under 4 min) or `medium`, picks the top result by view count + relevance. Returns: `{youtube_id, title, thumbnail, duration_seconds, url}`. Outputs the video recommendation.

4. **Daytona Live Rewrite Node (custom Python node)** — Reconnects to existing sandbox:
   - `sandbox_id` retrieved from Butterbase KV
   - `daytona.get(sandbox_id)` reconnects
   - Agent writes updated level code to `sandbox.fs` (`level_{N}.py`)
   - `sandbox.process.exec("python reload_level.py {N}")` hot-reloads just that level
   - Game continues from where child left off, now with the replanned level
   - Outputs: `{replan_applied: true, new_level_config}`

5. **Output Node** — Writes replan event to `session_events` in Butterbase. Writes video recommendation to `video_recommendations` table. Pushes realtime event on `"child:{child_id}:session"` channel with payload `{event: "replan", video: {...}, explanation: "..."}`.

---

### Pipeline 3 — Memory Ingestion & Report Generation

**Trigger:** Butterbase realtime event on `"child:{child_id}:session"` with `{event: "session_end", session_id}`

**Source Node:** Webhook, receives full session summary assembled by Butterbase durable actor

**Node sequence and logic:**

1. **Session Assembly Node** — Queries Butterbase REST API for all `session_events` belonging to this session. Constructs a structured session JSON:
   ```json
   {
     "child_id": "...",
     "session_id": "...",
     "date": "...",
     "total_minutes": 24,
     "levels_completed": [...],
     "levels_failed": [...],
     "replan_events": [...],
     "videos_watched": [...],
     "attention_arc": [{minute: 0, errors: 0}, {minute: 5, errors: 1}, ...],
     "completion_rate": 0.82,
     "medication_logged": {time_delta_minutes: 45, medication: "methylphenidate"}
   }
   ```

2. **Cognee Ingest Node (custom Python node)** — Three sequential operations:
   - `cognee.remember(session_json, user_set=child_id)` → ingests raw data
   - `cognee.cognify()` → ECL pipeline runs: classifies session, extracts entity-relationship triples (child struggled with fractions at minute 14, video on visual fractions helped, replan reduced errors), embeds all, commits to Neo4j
   - `cognee.memify()` → refines the memory graph: increases edge weight on recurring struggle patterns, prunes one-off anomalies, adds derived temporal facts if applicable

3. **Neo4j GDS Analysis Node (custom Python node)** — Runs three queries:
   - `gds.betweenness.centrality` on this child's concept graph → returns the #1 bottleneck concept by centrality score
   - `gds.pageRank` on struggle event nodes → returns the most impactful recurring struggle
   - Cypher query: attention arc trend over last 5 sessions (aggregated from `session_events` nodes in Neo4j) → returns whether attention window is expanding, stable, or contracting

4. **LLM Report Node (strong model via Butterbase AI gateway)** — Receives: GDS analysis results, Cognee recall of child's full history (`cognee.search("overall progress summary", search_type="GRAPH_COMPLETION")`), medication correlation data if available, this session's raw stats. Generates:
   - Parent summary: 3-sentence plain-English summary of what happened
   - Doctor full report: attention arc chart data, concept bottleneck ranking, struggle pattern taxonomy, medication correlation insight (if logged), recommended next session structure
   - Next session recommendations: which topics to prioritize, suggested session duration

5. **Output Node** — Writes report to Butterbase `reports` table. Updates `sessions.status = "complete"`. Triggers Butterbase webhook to doctor notification endpoint. Pushes `{event: "report_ready"}` on parent realtime channel. Stops Daytona sandbox (`sandbox.stop()`) to preserve state without burning compute.

---

## 6. Feature Logic

### Feature 1 — PDF to Personalized Game (the "wow" feature)

**Logic chain:**

```
PDF arrives → OCR extracts text → NER identifies questions →
LLM classifies each question → Cognee prior memory recalled →
LLM generates game spec (personalized level order) →
Daytona agent writes game to sandbox → game validated →
game URL returned to parent in < 90 seconds
```

**What "personalized level order" means concretely:**
- Default: order questions easy → hard (difficulty 1 → 5)
- With Cognee memory: if child historically struggles after 12 minutes, place all hard questions before minute 10
- If child struggles with fractions, place a confidence-building division level immediately before the first fraction level
- If child's prior session ended on a failure, start this session with an easy question to restore confidence

**Game mechanic assignment logic:**
- `division` → maze (navigate to the right quotient)
- `fractions` → visual matching (match fraction tiles)
- `word_problems` → dialogue-style quest (read, pick the right answer path)
- `addition/subtraction` → speed round (time-limited scoring)
- General rule: mechanic variety prevents repetitive fatigue; no more than 2 consecutive levels of the same mechanic

**Attention checkpoints:** At intervals defined by `attention_baseline_minutes / 3`, the game inserts a low-effort "breather" level (a very easy question with a reward animation). This pacing is specific to this child's baseline.

---

### Feature 2 — Real-Time Struggle Detection & Replan

**Trigger condition:** 3 consecutive failures on the same level within one session

**The fail counter logic:**
- Durable actor increments `fail_count_by_level[current_level]` on each `level_fail` event
- Counter resets when the child moves to a different level
- At count = 3: actor fires the Pipeline 2 webhook with full context

**Replan is non-disruptive:** The child sees a brief animation ("Level updating…"), then the replanned level loads. The transition takes < 5 seconds because the Daytona sandbox is already warm.

**YouTube video logic:**
- `remaining_attention_seconds = attention_baseline_seconds - time_elapsed_seconds`
- If remaining < 120 seconds: skip video (too short to be useful), go straight to replanned level
- If remaining 120–300 seconds: filter for videos under 2 minutes
- If remaining > 300 seconds: filter for videos under 4 minutes
- Videos filtered to match child's grade level and exact concept tag (not just subject)

---

### Feature 3 — Cognee Self-Improving Memory

**What gets ingested per session:** Every level attempt (success, fail, time), every replan event, every video watched and whether the subsequent level improved, total session time, attention arc (errors over time), and any parent-logged medication timing.

**How memify improves the graph across sessions:**
- `struggle_with_fractions` edge: weight 0.3 after session 1, 0.6 after session 3, 0.9 after session 5 → by session 5, the system treats fraction difficulty as a near-certainty and always front-loads fraction levels early
- `video_helped` edges: if a video at a concept reliably reduces errors in the next level, that `VideoRecommendation → Concept` edge gets strengthened
- Stale nodes get pruned: if a topic was hard 3 sessions ago but easy in the last 2, the struggle edge weight decreases
- Derived temporal facts: "attention drops after 12 minutes on Tuesday evenings" is a derived fact added by memify if the pattern appears in 3+ sessions

---

### Feature 4 — Doctor Insight Dashboard

**What the doctor sees:**

1. **Attention arc trend** — line chart of `attention_window_minutes` over last 8 sessions, with session dates on x-axis
2. **Concept bottleneck heatmap** — ranked list of concepts by Neo4j GDS betweenness centrality score across all sessions. The concept with the highest score is the one blocking the most other concepts.
3. **Replan frequency trend** — sessions requiring 0, 1, 2, 3+ replans over time. Decreasing trend = system working.
4. **Medication correlation panel** (if medication logs exist) — scatter of `time_since_medication` vs `attention_window_minutes`. If correlation exists, Cognee GRAPH_COMPLETION surfaces it as a cited insight.
5. **Cognee Q&A panel** — doctor types "Has this child improved on division over the last month?" → Cognee's `GRAPH_COMPLETION` retrieval traverses the knowledge graph and returns a cited answer with session references.

**Data access logic:**
- Doctor can only see children where `children.doctor_user_id = auth.uid()` (Butterbase RLS enforced at query level)
- Doctor can access full `report_json`; parent only sees `summary_text`

---

## 7. Team Split

### Ground Rules

- **No two people touch the same sponsor's integration code**
- **Each person owns their integration contracts** (inputs they accept, outputs they publish) and is the single source of truth for those
- **Integration points** are defined in Section 8 as shared contracts — not to be changed unilaterally
- **Team syncs** are needed at: game spec JSON format, session event payload format, report JSON format

---

### Person A — Backend Infrastructure & Memory

**Owns:** Butterbase setup, Cognee integration, Neo4j schema, data models

**Responsibilities:**

1. **Butterbase provisioning**
   - Create the Butterbase app
   - Define schema (all tables listed in Section 4) via declarative schema endpoint
   - Apply RLS policies (parent/doctor/child isolation)
   - Configure OAuth (Google login) for parent and doctor roles
   - Set up file storage bucket for PDF uploads (configure CORS, file size limits, content-type restrictions to PDF only)
   - Set up KV store with TTL rules (session state, sandbox ID)
   - Configure realtime channels: `child:{child_id}:session`
   - Deploy the YouTube Data API serverless function (Deno runtime on Butterbase)
   - Configure AI gateway with model routing rules (fast model → extraction tasks, strong model → generation + synthesis tasks)
   - Set up RAG collection: ingest curriculum prerequisite documents (grade 3–6 math topic dependency maps)
   - Configure durable actors for session state accumulation

2. **Neo4j schema setup**
   - Create all node labels and relationship types (see Section 4 graph schema)
   - Create indexes on `Child.id`, `Concept.name`, `Session.child_id`
   - Seed the prerequisite skill graph (`Concept → REQUIRES_UNDERSTANDING_OF → Concept`) for grades 3–6 math
   - Write and test all Cypher queries used in Pipeline 3 (betweenness centrality, pageRank, attention trend)
   - Configure Cognee to use Neo4j as its graph backend (`GRAPH_DATABASE_PROVIDER=neo4j`)

3. **Cognee setup**
   - Initialize Cognee with Neo4j backend + LanceDB vector store
   - Implement the `child_id` user isolation (Cognee user sets per child)
   - Test `cognify()` and `memify()` with synthetic session data
   - Test `recall()` returns expected behavioral context format
   - Test `search(type=GRAPH_COMPLETION)` for doctor Q&A
   - Implement `forget(dataset=child_id)` endpoint (account deletion compliance)

4. **Session event durable actor logic**
   - Define event accumulation logic inside Butterbase durable actor
   - Implement fail counter per level
   - Implement trigger logic for Pipeline 2 webhook (on fail_count >= 3)
   - Implement trigger logic for Pipeline 3 webhook (on session_end event)

**Deliverables to hand off to Person B:**
- Butterbase app credentials + REST API base URL
- PDF storage bucket presigned URL generation endpoint
- KV read/write API for session state
- Realtime channel spec (what events flow on which channel)
- AI gateway endpoint + model routing spec
- Neo4j connection string + all Cypher query specs
- Cognee instance URL + user set naming convention

---

### Person B — RocketRide Pipelines & Agent Orchestration

**Owns:** All three RocketRide pipelines, the multi-agent logic inside them, and the Daytona sandbox lifecycle

**Responsibilities:**

1. **RocketRide setup**
   - Install RocketRide VS Code extension
   - Deploy RocketRide Cloud project (or local + Docker during dev)
   - Configure all 13 LLM providers via connection manager (needs Butterbase AI gateway endpoint from Person A)
   - Configure Neo4j connection for the GDS query custom nodes

2. **Pipeline 1 — Ingestion & Game Generation**
   - Build the pipeline in RocketRide VS Code canvas (visual node graph)
   - Implement OCR node: accepts presigned PDF URL, outputs raw text
   - Implement NER node: outputs question list with topic + difficulty tags
   - Implement assignment metadata LLM node (fast model)
   - Implement custom Python node for Cognee `recall()` call (uses Cognee connection from Person A)
   - Implement game spec LLM node (strong model, uses Butterbase RAG context)
   - Implement Daytona Game Builder custom node (see Daytona logic in Section 5)
   - Implement output node: writes to Butterbase REST API, triggers realtime push

3. **Pipeline 2 — Struggle Replan**
   - Build the pipeline canvas
   - Implement Neo4j GDS shortest-path custom node (Cypher + GDS procedure)
   - Implement replan strategy LLM node
   - Implement Butterbase serverless function call node (YouTube lookup)
   - Implement Daytona Live Rewrite node (reconnect, write, hot-reload)
   - Implement output node: writes events + video rec to Butterbase

4. **Pipeline 3 — Memory & Report**
   - Build the pipeline canvas
   - Implement Session Assembly node (queries Butterbase REST API)
   - Implement Cognee Ingest node: `remember() → cognify() → memify()` sequence
   - Implement Neo4j GDS Analysis node: centrality + pageRank + Cypher trend queries
   - Implement LLM Report node (strong model via Butterbase gateway)
   - Implement output node: writes report to Butterbase, stops Daytona sandbox

5. **Daytona snapshot preparation**
   - Create the `adhdquest-pygame-base` snapshot image once:
     - Python 3.12 base
     - Install: pygame, turtle, pyglet, flask (for WebSocket game server)
     - Include: game template library files (level scaffolding, score tracker, hot-reload script)
   - Register snapshot in Daytona dashboard
   - Test: `daytona.create(snapshot="adhdquest-pygame-base")` completes in < 90ms
   - Test: game agent write-run-observe loop works within the sandbox

6. **Game template library design** (logic only — no full implementation)
   - Level template: accepts `{question_text, mechanic_type, difficulty}` JSON, renders appropriate mechanic
   - Score tracker: tracks fail count per level, emits events to Butterbase
   - Hot-reload script: `reload_level.py N` replaces level N's logic without restarting the game process
   - Attention checkpoint renderer: displays breather level at predefined intervals

**Deliverables to hand off to Person C:**
- Pipeline webhook URLs (all three pipelines)
- Game URL format returned by Pipeline 1
- Session event payload spec (what events the game emits to Butterbase)
- Realtime event specs (what the parent dashboard listens for)
- Report JSON schema (structure of the report document)

---

### Person C — Frontend & Doctor Dashboard

**Owns:** All UI — parent upload flow, game embedding, parent post-session view, doctor dashboard

**Responsibilities:**

1. **Parent Upload Flow**
   - Simple form: select child profile (if multiple children), upload PDF
   - On upload: POST PDF to Butterbase file storage endpoint, receive assignment_id
   - Show loading state: "Generating your game…" with a progress indicator
   - Subscribe to Butterbase realtime channel `child:{child_id}:session`
   - On `game_ready` event: render game frame with the returned URL

2. **Game Frame**
   - Embed the Daytona game preview URL in an iframe
   - Listen for realtime events on the session channel:
     - `replan` event: show brief overlay "Adjusting your game…", display YouTube video recommendation (title, thumbnail, duration, link), dismiss overlay after video or after 5 seconds
     - `session_end` event: transition to post-session report view
   - Parent sidebar (live, updates via realtime):
     - Current level number
     - Levels completed / total
     - Current streak vs fail count indicator (non-alarming — just a progress bar)

3. **Post-Session Parent Report**
   - On session complete: pull `reports` row from Butterbase REST API
   - Display: summary_text (LLM-generated plain English), completion percentage, attention arc (simple line chart), and a list of video recommendations shown during session
   - "Share with doctor" button: updates `children.doctor_user_id` (if not already set) — sends invite link to doctor

4. **Doctor Dashboard**
   - Doctor login (separate OAuth flow, role = doctor)
   - Can see all children where `doctor_user_id = auth.uid()`
   - Per-child view:
     - **Attention arc trend**: line chart across last 8 sessions (data from Neo4j Cypher query, served via Butterbase REST)
     - **Concept bottleneck ranking**: ranked list from GDS betweenness centrality stored in report_json
     - **Replan frequency trend**: bar chart of replans per session over time
     - **Medication correlation panel**: shown only if parent has logged medication. Scatter chart: x = time since medication (minutes), y = attention window that session. Data sourced from `medication_logs` joined with `sessions` via Butterbase REST.
     - **Cognee Q&A**: text input → POST to a Butterbase serverless function that calls `cognee.search(query, type="GRAPH_COMPLETION", user_set=child_id)` → returns cited answer rendered in the UI

5. **Tech stack for frontend**
   - React SPA (deployable to Butterbase frontend hosting with one command)
   - Butterbase TypeScript SDK for auth, REST calls, and realtime subscriptions
   - Chart library (Recharts or similar) for all graphs
   - No backend server needed — all API calls go through Butterbase directly

**Deliverables:**
- Deployed frontend on Butterbase hosting
- Working parent flow (upload → game → report)
- Working doctor dashboard with all 5 panels

---

### Parallel Work Timeline

```
Day 1 (Setup)
  Person A: Butterbase app creation, schema definition, RLS, Neo4j schema + seed data
  Person B: RocketRide Cloud project, Daytona snapshot creation, pipeline canvas setup
  Person C: React project scaffold, Butterbase SDK integration, auth flow

Day 2 (Core Build)
  Person A: Cognee setup, durable actor logic, serverless YouTube function, RAG ingestion
  Person B: Pipeline 1 (OCR → NER → LLM → game spec) — get to Daytona game builder node
  Person C: Parent upload UI, loading state, realtime subscription scaffolding

Day 3 (Integration)
  Person A: Test all Butterbase endpoints, test Cognee recall with dummy data, finalize KV TTL logic
  Person B: Complete Pipeline 1 (Daytona game builder → output node). Begin Pipeline 2.
  Person C: Embed game frame, listen for realtime events. Build post-session report view.

Day 4 (Full Loop)
  Person A: Test full Neo4j GDS queries. Support Person B with query debugging.
  Person B: Complete Pipeline 2 (replan). Complete Pipeline 3 (memory + report).
  Person C: Doctor dashboard (all 5 panels). Wire Cognee Q&A via Butterbase serverless function.

Day 5 (Polish + Demo Prep)
  All: End-to-end run-through with a real 5th-grade PDF
  All: Fix integration issues at contract boundaries
  All: Rehearse 8-minute demo flow
```

---

## 8. Integration Contracts

These are the shared data shapes that cross person boundaries. No one changes these without team agreement.

### Contract A: PDF Upload → Pipeline 1 Webhook

Person A fires this. Person B receives it.

```json
{
  "child_id": "uuid",
  "assignment_id": "uuid",
  "pdf_storage_url": "presigned_url_string",
  "child_profile": {
    "grade": 5,
    "attention_baseline_minutes": 15
  }
}
```

### Contract B: Pipeline 1 Output → Butterbase + Person C

Person B writes this. Person A stores it. Person C reads it.

```json
{
  "session_id": "uuid",
  "game_url": "https://sandbox-preview.daytona.io/...",
  "sandbox_id": "daytona_sandbox_id_string",
  "level_map": [
    {"level_index": 0, "question_id": "uuid", "topic": "division", "difficulty": 2},
    ...
  ],
  "estimated_session_minutes": 20
}
```

### Contract C: Realtime Events (Butterbase channel)

Person A defines the channel. Person B publishes to it. Person C subscribes to it.

```json
// game_ready
{"event": "game_ready", "game_url": "string", "level_count": 12}

// replan
{
  "event": "replan",
  "trigger_level": 4,
  "strategy": "prerequisite_inject",
  "explanation": "Adding a simpler fractions level first",
  "video": {
    "youtube_id": "string",
    "title": "string",
    "thumbnail_url": "string",
    "duration_seconds": 180,
    "url": "string"
  }
}

// session_end
{"event": "session_end", "session_id": "uuid", "report_id": "uuid"}
```

### Contract D: Session Event Payload (game → Butterbase)

Person B defines what the game emits. Person A stores it. Person C displays it.

```json
{
  "session_id": "uuid",
  "event_type": "level_complete | level_fail | session_end",
  "level_index": 3,
  "timestamp": "ISO8601",
  "payload": {
    "time_on_level_seconds": 47,
    "fail_count": 1,
    "score": 850
  }
}
```

### Contract E: Report JSON Schema

Person B generates this. Person A stores it. Person C renders it.

```json
{
  "session_summary": {
    "total_minutes": 22,
    "levels_completed": 9,
    "levels_total": 12,
    "completion_rate": 0.75,
    "replan_count": 1,
    "videos_watched": 1
  },
  "attention_arc": [
    {"minute": 0, "errors": 0},
    {"minute": 5, "errors": 1},
    ...
  ],
  "concept_performance": [
    {"concept": "division", "avg_time_seconds": 28, "fail_rate": 0.1},
    {"concept": "fractions", "fail_rate": 0.6, "replan_triggered": true}
  ],
  "bottleneck_concept": "fractions",
  "bottleneck_centrality_score": 0.87,
  "parent_summary": "Your child completed 9 out of 12 levels today...",
  "doctor_narrative": "Session 4 shows a continued struggle with fraction operations...",
  "next_session_recommendations": {
    "suggested_duration_minutes": 18,
    "prioritize_concepts": ["fractions"],
    "start_with_concept": "division"
  },
  "medication_correlation": null
}
```

---

## 9. Demo Script

### Setup (before demo — 15 minutes before)

- Person B: Upload the pre-prepared 5th-grade math PDF assignment manually to test the pipeline once, confirm game URL generates cleanly
- Person A: Confirm Neo4j browser shows child's learning graph with 2–3 prior sessions pre-seeded (for rich Cognee recall during demo)
- Person C: Open parent view, doctor view, and Neo4j Bloom in separate browser tabs

### Live Demo Flow (8 minutes)

**[0:00 – 1:00] — The problem statement**
Show a real scanned 5th-grade worksheet on screen. "This is what homework looks like. An ADHD kid sees this and shuts down."

**[1:00 – 2:30] — PDF upload → pipeline fires**
Parent uploads the PDF in the app. Show the RocketRide VS Code pipeline canvas in a split screen: watch nodes light up one by one as they execute — OCR node (raw text extracted), NER node (question tags appearing), LLM node (game spec generating). Narrate each node.

**[2:30 – 4:00] — Game appears**
Game URL arrives via Butterbase realtime. Game loads in the iframe. "This child has played 3 times before. Watch how the level order is already personalized — fractions come first because Cognee remembers this child struggles with them after 15 minutes." Show Cognee recall output in a sidebar.

**[4:00 – 5:30] — Struggle → replan → YouTube**
Presenter deliberately fails a fraction level 3 times. Pipeline 2 fires. Neo4j GDS shortest-path runs on screen (Bloom visualization). Replan explanation appears: "Adding a simpler step first." YouTube video appears on screen — a 2-minute visual fractions explanation fetched live from YouTube Data API.

**[5:30 – 7:00] — Session ends → report**
Close the game session. Pipeline 3 fires. Show Cognee ingesting the session in the terminal (entities appearing). Neo4j GDS betweenness centrality result: "fractions is the #1 concept bottleneck." Doctor dashboard loads. Show the attention arc chart and the Cognee Q&A: "Has this child improved on division?" → GRAPH_COMPLETION answer with session citations.

**[7:00 – 8:00] — Remove one sponsor**
"Remove Neo4j: Pipeline 2 has no prerequisite graph. We can't replan intelligently — we can only say try again. Remove Cognee: every session starts cold. Remove Daytona: the game has nowhere safe to run. Remove RocketRide: nothing connects. Remove Butterbase: no auth, no real-time, the parent never sees the game."

---

## 10. Dependency & Risk Register

| Risk | Owner | Mitigation |
|---|---|---|
| Daytona sandbox game preview URL has CORS issues with iframe | Person B | Test iframe embedding on day 1. Fallback: open game in new tab with a "Play Game" button |
| RocketRide OCR quality on low-res PDFs | Person B | Use a clean, typed PDF for demo. Pre-process PDF with higher DPI in the OCR node config |
| YouTube Data API quota (100 units/day free tier) | Person A | Pre-cache 10 video recommendations for the demo concepts. Fallback: return mock video data |
| Cognee cognify() takes > 30 seconds on first session | Person A | Pre-seed 3 prior sessions for the demo child before the presentation. Pipeline 3 only runs post-session, not live |
| Game pygame rendering doesn't work in browser iframe | Person B | Switch to a Flask + websocket game server running in sandbox, render via HTML canvas instead of pygame window |
| Neo4j GDS prerequisite graph not seeded with enough nodes | Person A | Seed grades 3–6 math curriculum graph on day 1 as first priority — all pipelines depend on it |
| RocketRide custom nodes (Cognee, Daytona, Neo4j GDS) don't have stable Python node SDK | Person B | Use RocketRide's Python-extensible node system. Test custom node execution on day 1. |
| Three people pushing to same Butterbase schema | Person A | Person A owns schema migrations exclusively. Others call REST endpoints only. |

---

*End of ADHDQuest Implementation Plan — v1.0*
