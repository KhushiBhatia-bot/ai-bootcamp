import chromadb

from .embeddings import generate_embedding


CHROMA_PATH = "data/vector_store"

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name="policy_chunks"
)


def add_chunks(
    policy_id: int,
    policy_name: str,
    chunks: list[dict],
):
    """
    Generate embeddings for policy chunks
    and store them in ChromaDB.
    """

    documents = []
    embeddings = []
    metadatas = []
    ids = []

    for index, chunk in enumerate(chunks):

        text = chunk["text"]
        page = chunk["page"]

        embedding = generate_embedding(
            text
        )

        documents.append(text)

        embeddings.append(embedding)

        metadatas.append(
            {
                "policy_id": str(policy_id),
                "policy_name": policy_name,
                "page": page,
            }
        )

        ids.append(
            f"policy_{policy_id}_chunk_{index}"
        )

    if documents:

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    return len(documents)