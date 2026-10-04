import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, SessionLocal
from app.dependencies.auth import get_current_user
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.models.llm_usage import LLMUsage
from app.schemas.message import (
    ChatMessageResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.llm_service import generate_response, generate_response_stream


router = APIRouter(
    prefix="/api/v1/chats/{chat_id}/messages",
    tags=["Messages"],
)


def get_user_chat(
    chat_id: int,
    current_user: User,
    db: Session,
) -> Chat:
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


@router.post("/", response_model=ChatMessageResponse)
async def create_message(
    chat_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Make sure this chat belongs to the logged-in user
    chat = get_user_chat(
        chat_id,
        current_user,
        db,
    )

    # Save user's message
    user_message = Message(
        chat_id=chat.id,
        role="user",
        content=message.content,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Load conversation history
    result = db.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at)
    )

    messages = result.scalars().all()

    conversation = [
        {
            "role": msg.role,
            "content": msg.content,
        }
        for msg in messages
    ]

    # Generate Qwen response
    answer, sources, tools_used, usage_stats = await generate_response(
        conversation
    )

    # Save assistant response
    assistant_message = Message(
    chat_id=chat.id,
    role="assistant",
    content=answer,
    )

    db.add(assistant_message)
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_message)
    
    # Save LLM usage stats
    llm_usage = LLMUsage(
        user_id=current_user.id,
        chat_id=chat.id,
        message_id=assistant_message.id,
        model_name=usage_stats["model_name"],
        prompt_tokens=usage_stats["prompt_tokens"],
        completion_tokens=usage_stats["completion_tokens"],
        total_tokens=usage_stats["total_tokens"],
        latency_ms=usage_stats["latency_ms"],
        tools_used=tools_used,
    )
    db.add(llm_usage)
    db.commit()

    return {
        "user_message": user_message,
        "assistant_message": assistant_message,
        "sources": sources,
        "tools_used": tools_used,
    }


@router.post("/stream")
async def stream_message(
    chat_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import logging as _logging
    _logging.getLogger("uvicorn.error").info(
        f"[STREAM] chat_id={chat_id} user_id={current_user.id} "
        f"content_len={len(message.content)} "
        f"content_preview={repr(message.content[:100])}"
    )
    # Verify chat ownership
    chat = get_user_chat(
        chat_id,
        current_user,
        db,
    )

    # Save user message
    user_message = Message(
        chat_id=chat.id,
        role="user",
        content=message.content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    user_msg_id = user_message.id
    user_id = current_user.id
    chat_model_id = chat.id

    # Load history
    result = db.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    conversation = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    async def event_generator():
        # First event: notify client of user message ID
        yield f"data: {json.dumps({'type': 'user_created', 'user_message_id': user_msg_id})}\n\n"

        full_content = ""
        sources = []
        tools_used = []
        usage_stats = {}

        try:
            async for event in generate_response_stream(conversation):
                event_type = event.get("type")
                if event_type == "done":
                    full_content = event.get("full_content", "")
                    sources = event.get("sources", [])
                    tools_used = event.get("tools_used", [])
                    usage_stats = event.get("usage_stats", {})
                yield f"data: {json.dumps(event)}\n\n"

            # Persist assistant response & usage into database in a fresh session
            with SessionLocal() as write_db:
                asst_msg = Message(
                    chat_id=chat_model_id,
                    role="assistant",
                    content=full_content,
                )
                write_db.add(asst_msg)
                
                chat_rec = write_db.query(Chat).filter(Chat.id == chat_model_id).first()
                if chat_rec:
                    chat_rec.updated_at = datetime.utcnow()
                write_db.commit()
                write_db.refresh(asst_msg)

                if usage_stats:
                    llm_usage = LLMUsage(
                        user_id=user_id,
                        chat_id=chat_model_id,
                        message_id=asst_msg.id,
                        model_name=usage_stats.get("model_name", "qwen"),
                        prompt_tokens=usage_stats.get("prompt_tokens", 0),
                        completion_tokens=usage_stats.get("completion_tokens", 0),
                        total_tokens=usage_stats.get("total_tokens", 0),
                        latency_ms=usage_stats.get("latency_ms", 0.0),
                        tools_used=tools_used,
                    )
                    write_db.add(llm_usage)
                    write_db.commit()

                # Send final confirmation with message ID for deletion capability
                yield f"data: {json.dumps({'type': 'persisted', 'assistant_message_id': asst_msg.id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



@router.get(
    "/",
    response_model=list[MessageResponse],
)
def get_messages(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership first
    chat = get_user_chat(
        chat_id,
        current_user,
        db,
    )

    result = db.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at)
    )

    return result.scalars().all()


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
)
def get_message(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify chat ownership
    chat = get_user_chat(
        chat_id,
        current_user,
        db,
    )

    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.chat_id == chat.id,
        )
        .first()
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    return message


@router.delete(
    "/{message_id}"
)
def delete_message(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify chat ownership
    chat = get_user_chat(
        chat_id,
        current_user,
        db,
    )

    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.chat_id == chat.id,
        )
        .first()
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    db.delete(message)
    db.commit()

    return {
        "message": "Message deleted successfully"
    }