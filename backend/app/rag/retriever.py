
import os

from .chroma_client import collection
from .embeddings import generate_embedding


def get_max_distance() -> float:
    """Return the configured maximum ChromaDB distance."""
    try:
        value = float(os.getenv("POLICYGUARD_MAX_DISTANCE", "400"))
    except ValueError:
        value = 400.0

    return max(0.0, value)


def search_policy(
    query: str,
    top_k: int = 5,
    max_distance: float | None = None,
) -> list[dict]:
    """
    Retrieve the closest policy chunks.

    Lower ChromaDB distances indicate closer matches. The distance
    cutoff is a configurable heuristic, not a calibrated relevance score.
    """
    query = query.strip()

    if not query or top_k < 1:
        return []

    total_chunks = collection.count()
    if total_chunks == 0:
        return []

    threshold = (
        get_max_distance()
        if max_distance is None
        else max(0.0, float(max_distance))
    )

    query_embedding = generate_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_chunks),
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    distances = (results.get("distances") or [[]])[0] or []

    matches = []

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        if not document or distance is None:
            continue

        distance = float(distance)

        if distance > threshold:
            continue

        metadata = metadata or {}

        matches.append({
            "text": document,
            "policy_name": metadata.get("policy_name"),
            "page": metadata.get("page"),
            "policy_id": metadata.get("policy_id"),
            "distance": distance,
        })

    return matches