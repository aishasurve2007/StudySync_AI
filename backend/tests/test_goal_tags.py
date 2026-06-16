"""Unit tests for extract_goal_tags — pure function, no DB needed."""
from app.services.goal_tags import extract_goal_tags


def test_spec_example_ml_interview():
    # The exact example from the spec.
    assert extract_goal_tags("Prepare machine learning interview", []) == [
        "interview",
        "machine learning",
    ]


def test_alias_expansion_ml():
    # "ML" must expand to the canonical "machine learning".
    tags = extract_goal_tags("Prepare ML interview", ["Statistics"])
    assert "machine learning" in tags
    assert "interview" in tags
    assert "statistics" in tags


def test_multiword_phrase_match():
    tags = extract_goal_tags("Build a full stack web development project", [])
    assert "web development" in tags
    assert "project" in tags


def test_output_is_sorted_and_deduped():
    tags = extract_goal_tags("machine learning ML machine learning", [])
    assert tags == sorted(set(tags))
    assert tags.count("machine learning") == 1


def test_empty_input_returns_empty_list():
    assert extract_goal_tags("", []) == []
    assert extract_goal_tags(None, None) == []


def test_fallback_when_no_vocabulary_hit():
    # Unknown words fall back to stopword-stripped tokens (never crashes,
    # never returns generic noise like "the"/"to").
    tags = extract_goal_tags("the quick brownfox", [])
    assert "the" not in tags
    assert "quick" in tags
