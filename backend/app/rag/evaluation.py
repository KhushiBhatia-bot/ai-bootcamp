
import json
from pathlib import Path

from backend.app.rag.retriever import search_policy


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATASET = (
    PROJECT_ROOT
    / "backend"
    / "tests"
    / "data"
    / "rag_evaluation.json"
)


def load_dataset(dataset_path=DEFAULT_DATASET):
    with open(dataset_path, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("Evaluation dataset must be a JSON list.")

    for item in dataset:
        if not item.get("query") or not item.get("relevant_terms"):
            raise ValueError(
                "Every test case needs a query and relevant_terms."
            )

    return dataset


def chunk_is_relevant(chunk, relevant_terms):
    text = chunk.get("text", "").casefold()

    return all(
        term.casefold() in text
        for term in relevant_terms
    )


def evaluate_retrieval(dataset_path=DEFAULT_DATASET, top_k=5):
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    dataset = load_dataset(dataset_path)

    if not dataset:
        raise ValueError("Evaluation dataset is empty.")

    results = []
    total_hits = 0
    total_relevant_chunks = 0
    total_retrieved_chunks = 0

    for item in dataset:
        chunks = search_policy(item["query"], top_k=top_k)

        relevant = [
            chunk
            for chunk in chunks
            if chunk_is_relevant(
                chunk, item["relevant_terms"]
            )
        ]

        hit = len(relevant) > 0
        total_hits += int(hit)
        total_relevant_chunks += len(relevant)
        total_retrieved_chunks += len(chunks)

        results.append({
            "id": item.get("id", ""),
            "query": item["query"],
            "hit": hit,
            "retrieved_count": len(chunks),
            "relevant_count": len(relevant),
            "distances": [
                round(float(chunk["distance"]), 3)
                for chunk in chunks
                if chunk.get("distance") is not None
            ],
        })

    query_count = len(dataset)

    return {
        "total_queries": query_count,
        "top_k": top_k,
        "hit_rate": round(total_hits / query_count, 4),
        "precision_at_k": round(
            total_relevant_chunks / (query_count * top_k),
            4,
        ),
        "queries_with_hits": total_hits,
        "total_retrieved_chunks": total_retrieved_chunks,
        "results": results,
    }
