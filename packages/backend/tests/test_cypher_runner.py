"""Tests for the .cypher statement splitter used by the Neo4j setup runner."""

from backend.setup.cypher_runner import split_statements


def test_splits_multiple_statements_and_strips_comments():
    script = """
    // a comment line
    CREATE CONSTRAINT a IF NOT EXISTS FOR (c:Child) REQUIRE c.id IS UNIQUE;
    CREATE INDEX b IF NOT EXISTS FOR (c:Concept) ON (c.name);  // trailing comment
    """
    stmts = split_statements(script)
    assert len(stmts) == 2
    assert stmts[0].startswith("CREATE CONSTRAINT a")
    assert stmts[1].startswith("CREATE INDEX b")
    assert "//" not in stmts[1]


def test_semicolon_inside_string_literal_is_not_a_split():
    script = "MERGE (n:Concept {note: 'a; b; c'}) RETURN n;"
    stmts = split_statements(script)
    assert len(stmts) == 1
    assert "'a; b; c'" in stmts[0]


def test_double_slash_inside_string_is_preserved():
    script = "MERGE (v:VideoRecommendation {url: 'https://x/y'}) RETURN v;"
    stmts = split_statements(script)
    assert len(stmts) == 1
    assert "https://x/y" in stmts[0]


def test_trailing_statement_without_semicolon():
    script = "MATCH (n) RETURN count(n) AS c"
    stmts = split_statements(script)
    assert stmts == ["MATCH (n) RETURN count(n) AS c"]


def test_empty_and_comment_only_input():
    assert split_statements("// only a comment\n\n") == []
