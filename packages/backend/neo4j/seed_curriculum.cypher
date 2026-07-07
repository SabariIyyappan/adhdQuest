// ADHDQuest — Prerequisite skill/concept graph seed (grades 3–6 math).
// DAY 1 PRIORITY: every replan (Pipeline 2) depends on this graph existing.
// Edge direction: (advanced)-[:REQUIRES_UNDERSTANDING_OF]->(foundation).
// This is a starter skeleton — expand with the full curriculum map.

// --- Concepts ---
UNWIND [
  {id: 'c_counting',        name: 'counting',                subject: 'math', grade_level: 1},
  {id: 'c_addition',        name: 'addition',                subject: 'math', grade_level: 2},
  {id: 'c_subtraction',     name: 'subtraction',             subject: 'math', grade_level: 2},
  {id: 'c_multiplication',  name: 'multiplication',          subject: 'math', grade_level: 3},
  {id: 'c_division',        name: 'division',                subject: 'math', grade_level: 4},
  {id: 'c_factors',         name: 'factors_and_multiples',   subject: 'math', grade_level: 4},
  {id: 'c_fractions',       name: 'fractions',               subject: 'math', grade_level: 4},
  {id: 'c_equiv_fractions', name: 'equivalent_fractions',    subject: 'math', grade_level: 5},
  {id: 'c_fraction_ops',    name: 'fraction_operations',     subject: 'math', grade_level: 5},
  {id: 'c_decimals',        name: 'decimals',                subject: 'math', grade_level: 5},
  {id: 'c_word_problems',   name: 'multi_step_word_problems', subject: 'math', grade_level: 6}
] AS c
MERGE (n:Concept {id: c.id})
  SET n.name = c.name, n.subject = c.subject, n.grade_level = c.grade_level;

// --- Prerequisite edges ---
UNWIND [
  ['c_addition',        'c_counting'],
  ['c_subtraction',     'c_counting'],
  ['c_multiplication',  'c_addition'],
  ['c_division',        'c_multiplication'],
  ['c_factors',         'c_multiplication'],
  ['c_fractions',       'c_division'],
  ['c_fractions',       'c_factors'],
  ['c_equiv_fractions', 'c_fractions'],
  ['c_fraction_ops',    'c_equiv_fractions'],
  ['c_decimals',        'c_fractions'],
  ['c_word_problems',   'c_fraction_ops'],
  ['c_word_problems',   'c_decimals']
] AS pair
MATCH (adv:Concept {id: pair[0]}), (found:Concept {id: pair[1]})
MERGE (adv)-[r:REQUIRES_UNDERSTANDING_OF]->(found)
  SET r.weight = 1.0;   // uniform cost; dijkstra reads this in Pipeline 2
