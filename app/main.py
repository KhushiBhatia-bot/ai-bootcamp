import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database import Base, engine
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.models.llm_usage import LLMUsage
from app.routes.chats import router as chat_router
from app.routes.messages import router as message_router
from app.routes.documents import router as document_router
from app.services.llm_service import generate_response
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router


logger = logging.getLogger("uvicorn.error")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResearchMate",
    description="AI Research Chatbot powered by Qwen",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    body = None
    try:
        body = await request.body()
        body = body[:500].decode("utf-8", errors="replace")  # log first 500 chars
    except Exception:
        pass
    logger.error(
        f"422 Validation Error on {request.method} {request.url}\n"
        f"Errors: {errors}\n"
        f"Body preview: {body}"
    )
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body_preview": body},
    )


class TestPrompt(BaseModel):
    prompt: str


@app.get("/")
async def root():
    return {
        "message": "Welcome to ResearchMate",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/test-qwen")
async def test_qwen(request: TestPrompt):
    answer, sources, tools, usage = await generate_response([{"role": "user", "content": request.prompt}])

    return {
        "response": answer
    }


app.include_router(chat_router)
app.include_router(message_router)
app.include_router(document_router)
app.include_router(auth_router)