"""Node-level unit + stress tests: OCR extraction and NER classification.

These are pure logic (no sponsor I/O) so they run without the mocks fixture.
"""

from __future__ import annotations

from pipelines.nodes import ner_node, ocr_node
from tests.helpers import FIXTURE


# --- OCR --------------------------------------------------------------

def test_ocr_reads_local_text_fixture() -> None:
    out = ocr_node.run(str(FIXTURE))
    assert "12 + 47" in out.raw_text
    assert out.page_count >= 1
    assert out.language == "en"


def test_ocr_file_uri_scheme() -> None:
    out = ocr_node.run("file://" + str(FIXTURE))
    assert out.raw_text.strip()


def test_ocr_counts_form_feed_pages(tmp_path) -> None:
    p = tmp_path / "multi.txt"
    p.write_text("page1\fpage2\fpage3", encoding="utf-8")
    assert ocr_node.run(str(p)).page_count == 3


# --- NER segmentation -------------------------------------------------

def test_ner_numbered_enumerators() -> None:
    text = "1. 2 + 2 = ?\n2) 9 - 4 = ?\nQ3: multiply 3 x 4"
    qs = ner_node.run(text)
    assert len(qs) == 3


def test_ner_falls_back_to_lines_without_enumerators() -> None:
    text = "5 + 5 = ?\nwhat is 8 divided by 2?\nsome heading with no math"
    qs = ner_node.run(text)
    # heading has no digit/operator/'?' -> dropped
    assert len(qs) == 2


def test_ner_empty_and_whitespace_return_no_questions() -> None:
    assert ner_node.run("") == []
    assert ner_node.run("   \n\t  ") == []
    assert ner_node.run("just a title with words") == []


# --- NER classification ----------------------------------------------

def test_ner_classifies_each_operation() -> None:
    cases = {
        "12 + 7 = ?": "addition",
        "20 - 8 = ?": "subtraction",
        "6 × 7 = ?": "multiplication",
        "Divide 56 by 8": "division",
        "What is 3/4 of 8?": "fractions",
        "Write 0.75 as a decimal": "decimals",
    }
    for text, expected in cases.items():
        (q,) = ner_node.run(text)
        assert q.topic == expected, f"{text!r} -> {q.topic}, expected {expected}"


def test_ner_fraction_slash_beats_division() -> None:
    (q,) = ner_node.run("Simplify 6/8")
    assert q.topic == "fractions"


def test_ner_word_problem_detection() -> None:
    (q,) = ner_node.run("Sarah has 15 apples and gives away 6, how many are left?")
    assert q.topic == "word_problem"


# --- NER difficulty ---------------------------------------------------

def test_ner_difficulty_bounds_1_to_5() -> None:
    text = "\n".join(f"{i}. {i} + {i} = ?" for i in range(1, 20))
    for q in ner_node.run(text):
        assert 1 <= q.difficulty <= 5


def test_ner_fractions_harder_than_addition() -> None:
    (add,) = ner_node.run("2 + 3 = ?")
    (frac,) = ner_node.run("Add 1/2 + 1/4")
    assert frac.difficulty > add.difficulty


def test_ner_large_numbers_bump_difficulty() -> None:
    (small,) = ner_node.run("2 + 3 = ?")
    (big,) = ner_node.run("128 + 356 = ?")
    assert big.difficulty > small.difficulty


def test_ner_multistep_bumps_difficulty() -> None:
    (one,) = ner_node.run("4 + 5 = ?")
    (multi,) = ner_node.run("4 + 5 - 2 = ?")
    assert multi.difficulty >= one.difficulty + 1
