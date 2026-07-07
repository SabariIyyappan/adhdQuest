"""Run multi-statement ``.cypher`` files against Neo4j.

The seed/schema/projection files are authored as human-readable scripts with
``//`` line comments and ``;``-terminated statements. The neo4j driver executes
one statement per call, so we strip comments and split on statement boundaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def split_statements(text: str) -> list[str]:
    """Split a Cypher script into individual statements.

    Removes ``//`` line comments and splits on top-level ``;``. Semicolons inside
    single- or double-quoted string literals are preserved.
    """
    no_comments: list[str] = []
    for line in text.splitlines():
        stripped = _strip_line_comment(line)
        if stripped.strip():
            no_comments.append(stripped)
    body = "\n".join(no_comments)

    statements: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in body:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            continue
        buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def _strip_line_comment(line: str) -> str:
    """Drop a trailing ``// comment``, ignoring ``//`` inside string literals."""
    quote: str | None = None
    for i in range(len(line) - 1):
        ch = line[i]
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "/" and line[i + 1] == "/":
            return line[:i]
    return line


def run_cypher_file(driver, path: Path, *, database: str = "neo4j") -> int:
    """Execute every statement in ``path``. Returns the count run."""
    statements = split_statements(Path(path).read_text(encoding="utf-8"))
    return run_statements(driver, statements, database=database)


def run_statements(driver, statements: Iterable[str], *, database: str = "neo4j") -> int:
    count = 0
    with driver.session(database=database) as session:
        for stmt in statements:
            session.run(stmt).consume()
            count += 1
    return count
