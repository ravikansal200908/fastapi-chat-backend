from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.auth import get_current_user
from app.db.postgres import get_db
from app.models.models import User, ChatRecord, Conversation
from app.schemas.schemas import (
    ChatRecordCreate,
    ChatRecord as ChatRecordSchema,
    ChatRecordUpdate,
    Conversation as ConversationSchema,
    ChatContent as ChatContentSchema
)
from app.db.mongodb import get_mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/create-chat", response_model=ChatRecordSchema, status_code=status.HTTP_201_CREATED)
async def create_chat(
    *,
    chat: ChatRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> Any:
    """
    Create a new chat record with initial conversation.
    
    Parameters:
    - chat: ChatRecordCreate object containing:
        - name: Name of the chat
        - chat_type: Type of chat (DIRECT, GROUP, CHANNEL)
        - active: Whether the chat is active
    
    Returns:
    - Created chat record
    
    Raises:
    - HTTPException(400): If chat creation fails
    """
    # Create chat record
    db_chat = ChatRecord(
        account_id=str(current_user.id),
        chat_type=chat.chat_type,
        name=chat.name,
        active=chat.active
    )
    db.add(db_chat)
    db.flush()  # Get the chat_id without committing

    # Create initial conversation
    conversation = Conversation(
        chat_id=db_chat.chat_id,
        account_id=str(current_user.id),
        name=chat.name
    )
    db.add(conversation)
    
    # Create MongoDB document
    chat_content = {
        "chat_id": str(db_chat.chat_id),
        "qa_pairs": []
    }
    await mongodb.chat_contents.insert_one(chat_content)
    
    db.commit()
    db.refresh(db_chat)
    return db_chat

@router.get("/", response_model=List[ChatRecordSchema])
@cache(expire=300)  # Cache for 5 minutes
async def get_chats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all chats for the current user with pagination.
    
    Parameters:
    - skip: Number of chats to skip (for pagination)
    - limit: Maximum number of chats to return
    
    Returns:
    - List of chat records
    
    Raises:
    - HTTPException(403): If user is not authenticated
    """
    chats = db.query(ChatRecord).filter(
        ChatRecord.account_id == str(current_user.id)
    ).offset(skip).limit(limit).all()
    return chats

@router.get("/{chat_id}", response_model=ChatRecordSchema)
@cache(expire=300)  # Cache for 5 minutes
async def get_chat(
    *,
    db: Session = Depends(get_db),
    chat_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific chat by ID.
    
    Parameters:
    - chat_id: UUID of the chat
    
    Returns:
    - Chat record
    
    Raises:
    - HTTPException(404): If chat not found
    - HTTPException(403): If user doesn't have access to the chat
    """
    chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return chat

@router.put("/{chat_id}", response_model=ChatRecordSchema)
async def update_chat(
    *,
    db: Session = Depends(get_db),
    chat_id: UUID,
    chat_in: ChatRecordUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a chat's metadata.
    
    Parameters:
    - chat_id: UUID of the chat
    - chat_in: ChatRecordUpdate object containing:
        - name: New name for the chat (optional)
        - active: New active status (optional)
    
    Returns:
    - Updated chat record
    
    Raises:
    - HTTPException(404): If chat not found
    - HTTPException(403): If user doesn't have access to the chat
    """
    chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    update_data = chat_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)
    
    db.commit()
    db.refresh(chat)
    return chat

@router.delete("/delete-chat/{chat_id}", response_model=dict)
async def delete_chat(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    chat_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a chat and its associated content.
    
    Parameters:
    - chat_id: UUID of the chat to delete
    
    Returns:
    - Success message
    
    Raises:
    - HTTPException(404): If chat not found
    - HTTPException(403): If user doesn't have access to the chat
    """
    # Get chat
    chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Delete associated conversation first
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == chat_id
    ).first()
    if conversation:
        db.delete(conversation)
    
    # Delete from PostgreSQL
    db.delete(chat)
    db.commit()
    
    # Delete from MongoDB
    await mongodb.chat_contents.delete_one({"chat_id": str(chat_id)})
    
    return {
        "status": "success",
        "message": f"Chat has been successfully deleted"
    }

