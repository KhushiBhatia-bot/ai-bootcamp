
import os
import re

from .chroma_client import collection
from .embeddings import generate_embedding


def search_policy(
    query: str,
    top_k: int = 5,
    max_distance: float | None = None,
    hyde_document: str | None = None,
) -> list[dict]:
    """Retrieve policy chunks using vector similarity."""
    query = query.strip()
    if hyde_document:
        hyde_document = hyde_document.strip()

    if not query or top_k < 1:
        return []

    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    if max_distance is None:
        try:
            max_distance = float(
                os.getenv("POLICYGUARD_MAX_DISTANCE", "400")
            )
        except ValueError:
            max_distance = 400.0

    text_to_embed = hyde_document if hyde_document else query
    embedding = generate_embedding(text_to_embed)

    results = collection.query(
        query_embeddings=[embedding],
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

        if distance > max_distance:
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


def search_policy_hybrid(
    query: str,
    top_k: int = 5,
    candidate_limit: int = 50,
    hyde_document: str | None = None,
) -> list[dict]:
    """Combine vector and keyword rankings using RRF."""
    query = query.strip()
    if hyde_document:
        hyde_document = hyde_document.strip()

    if not query or top_k < 1 or candidate_limit < 1:
        return []

    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    text_to_embed = hyde_document if hyde_document else query
    vector_results = collection.query(
        query_embeddings=[generate_embedding(text_to_embed)],
        n_results=min(candidate_limit, total_chunks),
        include=["documents", "metadatas", "distances"],
    )

    ids = (vector_results.get("ids") or [[]])[0] or []
    docs = (vector_results.get("documents") or [[]])[0] or []
    metas = (vector_results.get("metadatas") or [[]])[0] or []
    distances = (vector_results.get("distances") or [[]])[0] or []

    candidates = {}

    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(ids, docs, metas, distances), start=1
    ):
        if not document:
            continue

        candidates[chunk_id] = {
            "text": document,
            "metadata": metadata or {},
            "distance": (
                float(distance) if distance is not None else None
            ),
            "vector_rank": rank,
            "keyword_rank": None,
        }

    stored = collection.get(include=["documents", "metadatas"])

    terms = set(
        re.findall(r"\b[a-zA-Z0-9_-]+\b", query.casefold())
    )
    terms -= {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "for", "from", "how", "in", "is", "it", "of", "on",
        "or", "the", "to", "what", "when", "where", "which",
        "who", "why", "with", "should", "can", "could",
    }

    keyword_matches = []

    for chunk_id, document, metadata in zip(
        stored.get("ids") or [],
        stored.get("documents") or [],
        stored.get("metadatas") or [],
    ):
        if not document:
            continue

        text = document.casefold()
        matched = sum(term in text for term in terms)

        if matched == 0:
            continue

        score = matched / max(len(terms), 1)

        if query.casefold() in text:
            score += 1.0

        keyword_matches.append(
            (chunk_id, document, metadata or {}, score)
        )

    keyword_matches.sort(key=lambda item: item[3], reverse=True)

    for rank, (chunk_id, document, metadata, _) in enumerate(
        keyword_matches[:candidate_limit], start=1
    ):
        if chunk_id not in candidates:
            candidates[chunk_id] = {
                "text": document,
                "metadata": metadata,
                "distance": None,
                "vector_rank": None,
                "keyword_rank": rank,
            }
        else:
            candidates[chunk_id]["keyword_rank"] = rank

    for candidate in candidates.values():
        score = 0.0

        if candidate["vector_rank"] is not None:
            score += 1 / (60 + candidate["vector_rank"])

        if candidate["keyword_rank"] is not None:
            score += 1 / (60 + candidate["keyword_rank"])

        candidate["rrf_score"] = score

    ranked = sorted(
        candidates.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )

    return [
        {
            "text": item["text"],
            "policy_name": item["metadata"].get("policy_name"),
            "page": item["metadata"].get("page"),
            "policy_id": item["metadata"].get("policy_id"),
            "distance": item["distance"],
            "rrf_score": item["rrf_score"],
        }
        for item in ranked[:top_k]
    ]

