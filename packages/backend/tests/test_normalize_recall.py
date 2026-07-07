"""Tests for Cognee recall normalization into the stable prior_context shape."""

from backend.cognee.client import _EMPTY_CONTEXT, _normalize_recall


def test_cold_start_returns_well_formed_empty():
    ctx = _normalize_recall(None)
    for key in _EMPTY_CONTEXT:
        assert key in ctx
    assert ctx["struggle_topics"] == []
    assert ctx["attention_window_minutes"] is None
    assert ctx["raw"] is None


def test_parses_clean_json_answer():
    raw = [
        {
            "answer": (
                '{"struggle_topics": ["fractions", "decimals"], '
                '"attention_window_minutes": 12, '
                '"preferred_explanation_style": "visual", '
                '"last_session_summary": "completed 9/12", '
                '"medication_correlation": "better after meds"}'
            )
        }
    ]
    ctx = _normalize_recall(raw)
    assert ctx["struggle_topics"] == ["fractions", "decimals"]
    assert ctx["attention_window_minutes"] == 12
    assert ctx["preferred_explanation_style"] == "visual"
    assert ctx["medication_correlation"] == "better after meds"


def test_extracts_json_embedded_in_prose_and_fences():
    raw = "Here is the summary:\n```json\n{\"struggle_topics\": [\"fractions\"]}\n```\nThanks!"
    ctx = _normalize_recall(raw)
    assert ctx["struggle_topics"] == ["fractions"]


def test_prose_only_answer_falls_back_to_summary():
    raw = "The child struggles most with fraction operations after 12 minutes."
    ctx = _normalize_recall(raw)
    assert ctx["struggle_topics"] == []
    assert "fraction operations" in ctx["last_session_summary"]


def test_coerces_scalar_and_string_number_fields():
    raw = {"result": '{"struggle_topics": "fractions", "attention_window_minutes": "14"}'}
    ctx = _normalize_recall(raw)
    assert ctx["struggle_topics"] == ["fractions"]
    assert ctx["attention_window_minutes"] == 14
