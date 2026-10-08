import requests

OLLAMA_URL = "http://localhost:11434"
GENERATION_MODEL = "qwen3:8b"


def generate_answer(prompt: str) -> str:
    """Generate a response using local Qwen through Ollama."""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": GENERATION_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        },
        timeout=180,
    )

    response.raise_for_status()
    return response.json()["response"].strip()