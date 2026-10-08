import requests


OLLAMA_URL = "http://localhost:11434"

EMBEDDING_MODEL = "nomic-embed-text"


def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding using the local Ollama
    embedding model.
    """

    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["embedding"]