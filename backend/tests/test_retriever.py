
from unittest.mock import patch

from backend.app.rag.retriever import search_policy


@patch("backend.app.rag.retriever.collection")
@patch("backend.app.rag.retriever.generate_embedding")
def test_returns_matches_below_distance_cutoff(
    mock_embedding, mock_collection
):
    mock_collection.count.return_value = 2
    mock_embedding.return_value = [0.1, 0.2]

    mock_collection.query.return_value = {
        "documents": [["Relevant policy", "Unrelated text"]],
        "metadatas": [[
            {"policy_name": "Security", "page": 1, "policy_id": "1"},
            {"policy_name": "Other", "page": 2, "policy_id": "2"},
        ]],
        "distances": [[100.0, 500.0]],
    }

    results = search_policy(
        "How is data protected?",
        top_k=2,
        max_distance=400,
    )

    assert len(results) == 1
    assert results[0]["text"] == "Relevant policy"
    assert results[0]["page"] == 1
    assert results[0]["distance"] == 100.0


@patch("backend.app.rag.retriever.collection")
def test_empty_collection_returns_no_results(mock_collection):
    mock_collection.count.return_value = 0

    assert search_policy("Security policy") == []


@patch("backend.app.rag.retriever.collection")
def test_blank_query_returns_no_results(mock_collection):
    assert search_policy("   ") == []
    mock_collection.count.assert_not_called()