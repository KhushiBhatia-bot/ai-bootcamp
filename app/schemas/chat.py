from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    tag: Optional[str] = Field(default=None, max_length=50)


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    is_pinned: Optional[bool] = None
    tag: Optional[str] = Field(default=None, max_length=50)


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    is_pinned: bool = False
    tag: Optional[str] = None
    created_at: datetime
    updated_at: datetime