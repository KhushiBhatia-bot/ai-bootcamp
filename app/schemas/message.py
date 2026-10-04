from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=200000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class Source(BaseModel):
    title: str
    url: str
    snippet: str = ""


class ChatMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: list[Source] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)