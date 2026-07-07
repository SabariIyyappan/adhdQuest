# backend — Person A (Butterbase · Neo4j · Cognee)

Owns authentication, data persistence, role isolation, realtime, serverless compute,
LLM routing, the knowledge graph, and the self-improving child memory.

## Layout

```
schema/       Butterbase declarative Postgres schema + RLS policies.
functions/    Deno serverless functions deployed to Butterbase.
                youtube-lookup/   concept + attention window -> ranked video
                cognee-qa/        doctor GRAPH_COMPLETION Q&A endpoint
actors/       Durable actor: per-session state, fail counter, pipeline triggers.
neo4j/        Graph schema (constraints/indexes), curriculum seed, GDS queries.
cognee/       Cognee client wrappers: recall / remember / cognify / memify / forget.
config/       AI-gateway model routing + KV key conventions.
```

## Setup order (Day 1 priority)

1. Create the Butterbase app; apply `schema/tables.sql` then `schema/rls.sql`.
2. Configure OAuth (Google) for `parent` and `doctor` roles.
3. Stand up Neo4j; run `neo4j/schema.cypher` then `neo4j/seed_curriculum.cypher`
   (**seed first — all pipelines depend on the prerequisite graph**).
4. Point Cognee at Neo4j (`GRAPH_DATABASE_PROVIDER=neo4j`) + LanceDB.
5. Deploy the two Deno functions in `functions/`.

## Deliverables to Person B

See the plan §7. Hand off: REST base URL, presigned-URL endpoint, KV API,
realtime channel spec, AI-gateway endpoint, Neo4j connection string, Cognee URL.
