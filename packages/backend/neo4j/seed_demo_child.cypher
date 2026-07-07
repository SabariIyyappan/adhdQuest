// ADHDQuest — Demo child with prior sessions (plan §9 setup, §10 risk mitigation).
// Pre-seeds a rich learning history so Cognee recall + GDS analytics have something
// to reason about during the live demo. Safe to re-run (all MERGE / idempotent).
//
// Run AFTER schema.cypher, seed_curriculum.cypher, gds_projections.cypher.
// The child_id here must match the demo `children.id` row in Butterbase Postgres.

// --- Demo child ------------------------------------------------------
MERGE (c:Child {id: '00000000-0000-0000-0000-0000000000d1'})
  SET c.name = 'Demo Kid',
      c.grade = 5,
      c.attention_baseline_minutes = 15;

// --- Concepts this child has mastered (dijkstra source set) ----------
// These are the "current knowledge" the replan path terminates at.
UNWIND ['counting','addition','subtraction','multiplication','division','factors_and_multiples'] AS mastered_name
MATCH (c:Child {id: '00000000-0000-0000-0000-0000000000d1'}), (k:Concept {name: mastered_name})
MERGE (c)-[m:HAS_MASTERED]->(k)
  SET m.confidence_score = 0.9;

// --- Concepts this child struggles with (scopes GDS per child) -------
UNWIND [
  {name: 'fractions',           frequency: 4, avg_fail_count: 2.5},
  {name: 'fraction_operations', frequency: 3, avg_fail_count: 2.0},
  {name: 'equivalent_fractions', frequency: 2, avg_fail_count: 1.5}
] AS s
MATCH (c:Child {id: '00000000-0000-0000-0000-0000000000d1'}), (k:Concept {name: s.name})
MERGE (c)-[r:STRUGGLES_WITH]->(k)
  SET r.frequency = s.frequency, r.avg_fail_count = s.avg_fail_count;

// --- Three prior sessions (attention window is CONTRACTING over time) -
UNWIND [
  {id: 'sess-demo-1', date: date('2026-06-16'), total_minutes: 26, completion_rate: 0.85, attention_window_minutes: 16},
  {id: 'sess-demo-2', date: date('2026-06-23'), total_minutes: 22, completion_rate: 0.75, attention_window_minutes: 14},
  {id: 'sess-demo-3', date: date('2026-06-30'), total_minutes: 19, completion_rate: 0.66, attention_window_minutes: 12}
] AS sd
MATCH (c:Child {id: '00000000-0000-0000-0000-0000000000d1'})
MERGE (s:Session {id: sd.id})
  SET s.child_id = c.id,
      s.date = sd.date,
      s.total_minutes = sd.total_minutes,
      s.completion_rate = sd.completion_rate,
      s.attention_window_minutes = sd.attention_window_minutes
MERGE (c)-[:HAD_SESSION]->(s);

// --- Struggle events on those sessions, tagged to fraction concepts --
UNWIND [
  {sid: 'sess-demo-1', eid: 'strg-1', concept: 'fractions',           fail_count: 3, replan: true},
  {sid: 'sess-demo-2', eid: 'strg-2', concept: 'fractions',           fail_count: 2, replan: false},
  {sid: 'sess-demo-2', eid: 'strg-3', concept: 'fraction_operations', fail_count: 3, replan: true},
  {sid: 'sess-demo-3', eid: 'strg-4', concept: 'fraction_operations', fail_count: 3, replan: true},
  {sid: 'sess-demo-3', eid: 'strg-5', concept: 'equivalent_fractions', fail_count: 2, replan: false}
] AS se
MATCH (s:Session {id: se.sid}), (k:Concept {name: se.concept})
MERGE (e:StruggleEvent {id: se.eid})
  SET e.session_id = se.sid, e.fail_count = se.fail_count, e.replan_triggered = se.replan
MERGE (s)-[:HAD_STRUGGLE]->(e)
MERGE (e)-[:ON_CONCEPT]->(k);

// --- A video that reliably helped on fractions -----------------------
MERGE (v:VideoRecommendation {id: 'vid-demo-1'})
  SET v.youtube_id = 'dQw4w9WgXcQ', v.concept = 'fractions', v.duration_seconds = 150
WITH v
MATCH (k:Concept {name: 'fractions'})
MERGE (v)-[:EXPLAINS]->(k);

// --- Medication log preceding the most recent session ----------------
MERGE (m:MedicationLog {id: 'med-demo-1'})
  SET m.child_id = '00000000-0000-0000-0000-0000000000d1',
      m.timestamp = datetime('2026-06-30T15:15:00'),
      m.medication = 'methylphenidate',
      m.dose = 10.0
WITH m
MATCH (s:Session {id: 'sess-demo-3'})
MERGE (m)-[p:PRECEDED]->(s)
  SET p.time_delta_minutes = 45;
