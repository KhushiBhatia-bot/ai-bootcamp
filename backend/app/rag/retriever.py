from .chroma_client import collection
from .embeddings import generate_embedding

def search_policy(query: str, top_k: int = 5):
    """Find the most relevant policy chunks for a question."""


    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    query_embedding = generate_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_chunks),
    )

    matches = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        matches.append({
            "text": document,
            "policy_name": metadata.get("policy_name"),
            "page": metadata.get("page"),
            "policy_id": metadata.get("policy_id"),
            "distance": distance,
        })

    return matches

