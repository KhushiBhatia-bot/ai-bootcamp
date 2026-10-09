import json
from pathlib import Path
from unittest.mock import patch

from backend.app.api.chat import evaluate_policy


TEST_CASES = Path(__file__).with_name("test_cases.json")


def load_test_cases():
    with TEST_CASES.open(encoding="utf-8") as file:
        return json.load(file)


def test_empty_scenario_is_rejected():
    from backend.app.api.chat import ask_policy

    try:
        ask_policy("   ")
        assert False, "Expected ValueError for an empty question"
    except ValueError:
        pass


@patch("backend.app.api.chat.search_policy", return_value=[])
def test_no_evidence_returns_needs_review(mock_search):
    result = evaluate_policy(
        "A contractor requests an unusual access exception."
    )

    assert result["status"] == "NEEDS_REVIEW"
    assert result["retrieved_chunks"] == 0
    assert result["evidence"] == []
    mock_search.assert_called_once()


def test_evaluation_cases_have_required_fields():
    cases = load_test_cases()

    assert len(cases) >= 4

    for case in cases:
        assert case["scenario"].strip()
        assert case["expected_status"] in {
            "COMPLIANT",
            "NON_COMPLIANT",
            "NEEDS_REVIEW",
        }
        assert case["expected_policy_topic"].strip()