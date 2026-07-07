// ADHDQuest — Neo4j graph schema (plan §4).
// Constraints + indexes. Cognee-managed nodes coexist with these schema nodes
// in the same instance (GRAPH_DATABASE_PROVIDER=neo4j). Run once at setup.

// --- Uniqueness constraints (also create backing indexes) ---
CREATE CONSTRAINT child_id       IF NOT EXISTS FOR (c:Child)               REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT session_id     IF NOT EXISTS FOR (s:Session)             REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT question_id    IF NOT EXISTS FOR (q:Question)            REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT skill_id       IF NOT EXISTS FOR (k:Skill)               REQUIRE k.id IS UNIQUE;
CREATE CONSTRAINT struggle_id    IF NOT EXISTS FOR (e:StruggleEvent)       REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT concept_id     IF NOT EXISTS FOR (c:Concept)             REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT video_id       IF NOT EXISTS FOR (v:VideoRecommendation) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT medlog_id      IF NOT EXISTS FOR (m:MedicationLog)       REQUIRE m.id IS UNIQUE;

// --- Lookup indexes used by pipelines ---
CREATE INDEX concept_name  IF NOT EXISTS FOR (c:Concept) ON (c.name);
CREATE INDEX session_child IF NOT EXISTS FOR (s:Session) ON (s.child_id);

// Node labels & relationships (for reference — created implicitly by MERGE):
//   (:Child)-[:HAD_SESSION]->(:Session)
//   (:Session)-[:CONTAINED_QUESTION]->(:Question)
//   (:Session)-[:HAD_STRUGGLE]->(:StruggleEvent)-[:ON_CONCEPT]->(:Concept)
//   (:Concept)-[:REQUIRES_UNDERSTANDING_OF]->(:Concept)   // THE PREREQUISITE GRAPH
//   (:Child)-[:HAS_MASTERED]->(:Concept)   // dijkstra source set (Pipeline 2)
//   (:Child)-[:HAS_MASTERED]->(:Skill)     // fine-grained skill confidence (optional)
//   (:Child)-[:STRUGGLES_WITH]->(:Concept) // scopes GDS centrality/pageRank per child
//   (:VideoRecommendation)-[:EXPLAINS]->(:Concept)
//   (:MedicationLog)-[:PRECEDED]->(:Session)
//
// GDS: after this schema + the seed files are loaded, run gds_projections.cypher
// to materialize the in-memory graphs (prereqGraph, childStruggleGraph) that
// queries.cypher depends on.
