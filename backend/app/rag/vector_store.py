from .chroma_client import collection
from .embeddings import generate_embedding

def add_chunks(
policy_id: int,
policy_name: str,
chunks: list[dict],
):
    """Generate embeddings and store policy chunks in ChromaDB."""


    documents = []
    embeddings = []
    metadatas = []
    ids = []

    for index, chunk in enumerate(chunks):
        text = chunk["text"]
        page = chunk["page"]

        embedding = generate_embedding(text)

        documents.append(text)
        embeddings.append(embedding)

        metadatas.append({
            "policy_id": str(policy_id),
            "policy_name": policy_name,
            "page": page,
        })

        ids.append(f"policy_{policy_id}_chunk_{index}")

    if documents:
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    return len(documents)

