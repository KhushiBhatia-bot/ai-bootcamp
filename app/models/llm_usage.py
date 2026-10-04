from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMUsage(Base):
    __tablename__ = "llm_usages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id"),
        index=True,
    )
    
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(50))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    latency_ms: Mapped[float] = mapped_column(Float)
    tools_used: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
