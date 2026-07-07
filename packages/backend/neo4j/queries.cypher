// ADHDQuest — Named Cypher/GDS queries used by the pipelines.
// The RocketRide custom nodes (packages/pipelines/nodes/neo4j_gds_node.py) load
// these by name and run each as a SINGLE statement. Rules:
//   - one statement per block (no extra `;`), params via $name
//   - the GDS graphs (prereqGraph, childStruggleGraph) are projected once by
//     gds_projections.cypher; these queries assume they already exist.

// ============================================================
// PIPELINE 2 — shortest prerequisite path (dijkstra)
// Params: $child_id, $blocked_concept
// Walks the prereq graph from the blocked concept down to the NEAREST concept
// the child has already mastered, then returns the path foundation-first so the
// replan node can inject the missing prerequisites in learning order.
// ============================================================
// name: prerequisite_path
MATCH (target:Concept {name: $blocked_concept})
MATCH (:Child {id: $child_id})-[:HAS_MASTERED]->(mastered:Concept)
WITH target, collect(elementId(mastered)) AS mastered_ids
CALL gds.allShortestPaths.dijkstra.stream('prereqGraph', {
  sourceNode: target,
  relationshipWeightProperty: 'weight'
})
YIELD targetNode, totalCost, nodeIds
WHERE elementId(gds.util.asNode(targetNode)) IN mastered_ids
WITH nodeIds, totalCost
ORDER BY totalCost ASC
LIMIT 1
RETURN reverse([nid IN nodeIds | gds.util.asNode(nid).name]) AS prerequisite_path

// ============================================================
// PIPELINE 3 — bottleneck concept (betweenness centrality)
// Params: $child_id
// Betweenness is computed on the whole prerequisite graph, then restricted to the
// concepts THIS child struggles with → the child's most structurally-blocking gap.
// ============================================================
// name: bottleneck_centrality
CALL gds.betweenness.stream('prereqGraph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS concept, score
MATCH (:Child {id: $child_id})-[:STRUGGLES_WITH]->(concept)
RETURN concept.name AS concept, score
ORDER BY score DESC
LIMIT 5

// ============================================================
// PIPELINE 3 — most influential struggle concepts (pageRank)
// Params: $child_id
// PageRank over the prereq graph, restricted to the child's struggle concepts →
// which gap most propagates to the rest of their learning.
// ============================================================
// name: struggle_pagerank
CALL gds.pageRank.stream('prereqGraph', { relationshipWeightProperty: 'weight' })
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS concept, score
MATCH (:Child {id: $child_id})-[:STRUGGLES_WITH]->(concept)
RETURN concept.name AS concept, score
ORDER BY score DESC
LIMIT 5

// ============================================================
// PIPELINE 3 — attention window trend over last N sessions
// Params: $child_id, $limit
// ============================================================
// name: attention_trend
MATCH (c:Child {id: $child_id})-[:HAD_SESSION]->(s:Session)
RETURN s.date AS date, s.attention_window_minutes AS attention_window_minutes
ORDER BY s.date DESC
LIMIT $limit

// ============================================================
// DOCTOR DASHBOARD — similar-profile children (nodeSimilarity)
// Runs on the bipartite childStruggleGraph. Rebuild that projection on the
// weekly doctor cron before calling this.
// ============================================================
// name: similar_children
CALL gds.nodeSimilarity.stream('childStruggleGraph')
YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, similarity
WHERE a:Child AND b:Child
RETURN a.id AS child_a, b.id AS child_b, similarity
ORDER BY similarity DESC
LIMIT 10
