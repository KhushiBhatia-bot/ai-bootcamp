from pathlib import Path
import chromadb

# Project root: ai-bootcamp

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CHROMA_PATH = str(PROJECT_ROOT / "frontend" / "data" / "vector_store")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="policy_chunks")
