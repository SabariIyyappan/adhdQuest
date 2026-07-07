// ADHDQuest — GDS in-memory graph projections (plan §3, §5).
//
// The named queries in queries.cypher run GDS algorithms against these projected
// graphs. GDS 2.x removed anonymous projections, so every named graph must be
// projected before an algorithm can read it. The setup runner (setup/neo4j_setup.py)
// executes this file AFTER schema.cypher + the seed files.
//
// IMPORTANT: GDS graphs live in memory. If Neo4j restarts, re-run this file
// (the setup runner exposes `--projections-only` for exactly this).
//
// Each statement is idempotent: drop-if-exists (failIfMissing=false) then project.

// --- prereqGraph -----------------------------------------------------
// The static prerequisite graph over Concepts. Feeds:
//   - prerequisite_path      (shortestPath.dijkstra, Pipeline 2)
//   - bottleneck_centrality  (betweenness, Pipeline 3)
//   - struggle_pagerank      (pageRank, Pipeline 3)
// Edge weight drives dijkstra cost.
CALL gds.graph.drop('prereqGraph', false) YIELD graphName
RETURN graphName;

CALL gds.graph.project(
  'prereqGraph',
  'Concept',
  { REQUIRES_UNDERSTANDING_OF: { properties: 'weight' } }
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;

// --- childStruggleGraph ----------------------------------------------
// Bipartite Child -[:STRUGGLES_WITH]-> Concept graph, used by the doctor
// dashboard's nodeSimilarity query (similar_children). Rebuild on a schedule
// (e.g. the weekly doctor cron) so newly-active children are included.
CALL gds.graph.drop('childStruggleGraph', false) YIELD graphName
RETURN graphName;

CALL gds.graph.project(
  'childStruggleGraph',
  ['Child', 'Concept'],
  { STRUGGLES_WITH: { orientation: 'UNDIRECTED' } }
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;
