from fastapi import FastAPI

app = FastAPI(
    title="PolicyGuard AI API",
    description="AI-powered policy compliance and RAG platform",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "PolicyGuard AI",
    }