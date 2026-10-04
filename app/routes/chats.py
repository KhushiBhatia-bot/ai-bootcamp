from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatResponse, ChatUpdate

router = APIRouter(prefix="/api/v1/chats", tags=["Chats"])


@router.post("/", response_model=ChatResponse)
def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_chat = Chat(
        title=chat.title,
        tag=chat.tag,
        is_pinned=False,
        user_id=current_user.id,
    )

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return new_chat


@router.get("/", response_model=list[ChatResponse])
def get_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(Chat.is_pinned.desc(), Chat.updated_at.desc(), Chat.created_at.desc())
    )

    return result.scalars().all()


@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return chat


@router.patch("/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: int,
    chat_data: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    if chat_data.title is not None:
        chat.title = chat_data.title

    if chat_data.is_pinned is not None:
        chat.is_pinned = chat_data.is_pinned

    if chat_data.tag is not None:
        chat.tag = chat_data.tag if chat_data.tag != "" else None

    db.commit()
    db.refresh(chat)

    return chat


@router.delete("/{chat_id}")
def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    db.delete(chat)
    db.commit()

    return {
        "message": "Chat deleted successfully"
    }