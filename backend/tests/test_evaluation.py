
from unittest.mock import patch

from backend.app.api.chat import evaluate_policy


@patch("backend.app.api.chat.generate_answer")
@patch("backend.app.api.chat.search_policy")
def test_valid_non_compliant_result(mock_search, mock_generate):
    mock_search.return_value = [
        {
            "policy_name": "Information Security Policy",
            "page": 3,
            "text": "Confidential data must not be stored in personal cloud accounts.",
            "distance": 100.0,
        }
    ]

    mock_generate.return_value = (
        "STATUS: NON_COMPLIANT\n"
        "REASON: The scenario uses a personal cloud account.\n"
        "POLICY: Information Security Policy\n"
        "PAGE: 3"
    )

    result = evaluate_policy(
        "An employee uploads confidential data to a personal cloud drive."
    )

    assert result["status"] == "NON_COMPLIANT"
    assert result["claimed_policy"] == "Information Security Policy"
    assert result["claimed_page"] == "3"
    assert result["retrieved_chunks"] == 1
    assert len(result["evidence"]) == 1


@patch("backend.app.api.chat.generate_answer")
@patch("backend.app.api.chat.search_policy")
def test_no_evidence_returns_needs_review(mock_search, mock_generate):
    mock_search.return_value = []

    result = evaluate_policy("An unrelated question")

    assert result["status"] == "NEEDS_REVIEW"
    assert result["retrieved_chunks"] == 0
    assert result["evidence"] == []
    mock_generate.assert_not_called()


@patch("backend.app.api.chat.generate_answer")
@patch("backend.app.api.chat.search_policy")
def test_invalid_model_status_returns_needs_review(
    mock_search, mock_generate
):
    mock_search.return_value = [
        {
            "policy_name": "Security Policy",
            "page": 1,
            "text": "Protect confidential information.",
            "distance": 100.0,
        }
    ]

    mock_generate.return_value = (
        "STATUS: MAYBE\n"
        "REASON: It might be acceptable."
    )

    result = evaluate_policy("A test scenario")

    assert result["status"] == "NEEDS_REVIEW"


def test_empty_scenario_raises_error():
    try:
        evaluate_policy("   ")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Scenario cannot be empty."

