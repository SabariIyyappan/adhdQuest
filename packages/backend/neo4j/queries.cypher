// ADHDQuest — Named Cypher/GDS queries used by the pipelines.
// The RocketRide custom nodes load these by name. Keep parameter names stable.

// ============================================================
// PIPELINE 2 — shortest prerequisite path (dijkstra)
// Params: $child_id, $blocked_concept
// Returns ordered prerequisite concepts from the nearest mastered ancestor
// down to the blocked concept.
// ============================================================
// name: prerequisite_path
CALL {
  WITH $child_id AS child_id, $blocked_concept AS blocked
  MATCH (target:Concept {name: blocked})
  // nearest ancestor the child has mastered
  MATCH (child:Child {id: child_id})-[:HAS_MASTERED]->(:Skill)<-[:*0..]-(mastered:Concept)
  WITH target, collect(mastered) AS mastered_concepts
  CALL gds.shortestPath.dijkstra.stream('prereqGraph', {
    sourceNode: target,
    targetNodes: mastered_concepts,
    relationshipWeightProperty: 'weight'
  })
  YIELD path
  RETURN [n IN nodes(path) | n.name] AS prerequisite_path
}
RETURN prerequisite_path;

// ============================================================
// PIPELINE 3 — bottleneck concept (betweenness centrality)
// Params: (runs on the child-projected subgraph 'childConceptGraph')
// ============================================================
// name: bottleneck_centrality
CALL gds.betweenness.stream('childConceptGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS concept, score
ORDER BY score DESC
LIMIT 5;

// ============================================================
// PIPELINE 3 — most impactful struggle patterns (pageRank)
// ============================================================
// name: struggle_pagerank
CALL gds.pageRank.stream('struggleGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS struggle_event, score
ORDER BY score DESC
LIMIT 5;

// ============================================================
// PIPELINE 3 — attention window trend over last N sessions
// Params: $child_id, $limit
// ============================================================
// name: attention_trend
MATCH (c:Child {id: $child_id})-[:HAD_SESSION]->(s:Session)
RETURN s.date AS date, s.attention_window_minutes AS attention_window_minutes
ORDER BY s.date DESC
LIMIT $limit;

// ============================================================
// DOCTOR DASHBOARD — similar-profile children (nodeSimilarity)
// ============================================================
// name: similar_children
CALL gds.nodeSimilarity.stream('childStruggleGraph')
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).id AS child_a,
       gds.util.asNode(node2).id AS child_b,
       similarity
ORDER BY similarity DESC
LIMIT 10;
