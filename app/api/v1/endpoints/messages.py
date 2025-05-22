from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID
from datetime import datetime

from app.core.auth import get_current_user
from app.db.postgres import get_db
from app.db.mongodb import get_mongodb
from app.models.models import User, Message, Conversation, ChatRecord
from app.schemas.schemas import MessageCreate, Message as MessageSchema
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/add-message", response_model=MessageSchema, status_code=status.HTTP_201_CREATED)
async def add_message(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Add a new message to a conversation.
    
    Parameters:
    - message_in: MessageCreate object containing:
        - content: The message content
        - conversation_id: UUID of the conversation
    
    Returns:
    - Created message object
    
    Raises:
    - HTTPException(404): If conversation not found
    - HTTPException(403): If user doesn't have access to the conversation
    """
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == message_in.conversation_id,
        Conversation.account_id == str(current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create message in PostgreSQL
    message = Message(
        content=message_in.content,
        conversation_id=message_in.conversation_id,
        user_id=current_user.id
    )
    db.add(message)
    db.flush()  # Get the message ID without committing
    
    # Add message to MongoDB
    qa_pair = {
        "question": message_in.content,
        "response": None,  # Response will be added later when AI responds
        "response_id": str(message.id),
        "timestamp": datetime.utcnow().isoformat(),
        "branches": []
    }
    
    await mongodb.chat_contents.update_one(
        {"chat_id": str(conversation.chat_id)},
        {"$push": {"qa_pairs": qa_pair}}
    )
    
    db.commit()
    db.refresh(message)
    return message

@router.get("/conversation/{conversation_id}", response_model=List[MessageSchema])
async def get_conversation_messages(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all messages in a conversation with pagination.
    
    Parameters:
    - conversation_id: UUID of the conversation
    - skip: Number of messages to skip (for pagination)
    - limit: Maximum number of messages to return
    
    Returns:
    - List of messages in the conversation
    
    Raises:
    - HTTPException(404): If conversation not found
    - HTTPException(403): If user doesn't have access to the conversation
    """
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == conversation_id,
        Conversation.account_id == str(current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages from PostgreSQL
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).offset(skip).limit(limit).all()
    
    return messages

@router.get("/{message_id}", response_model=MessageSchema)
async def get_message(
    *,
    db: Session = Depends(get_db),
    message_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific message by ID.
    
    Parameters:
    - message_id: UUID of the message
    
    Returns:
    - Message object
    
    Raises:
    - HTTPException(404): If message not found
    - HTTPException(403): If user doesn't have access to the message
    """
    message = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.account_id == str(current_user.id)
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message

@router.get("/get-chat/{chat_id}", response_model=List[MessageSchema])
@cache(expire=300)  # Cache for 5 minutes
async def get_chat(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all messages in a chat with caching.
    
    Parameters:
    - chat_id: UUID of the chat
    - skip: Number of messages to skip (for pagination)
    - limit: Maximum number of messages to return
    
    Returns:
    - List of messages in the chat
    
    Raises:
    - HTTPException(404): If chat not found
    - HTTPException(403): If user doesn't have access to the chat
    """
    # Verify chat exists and belongs to user
    chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Get messages from PostgreSQL with pagination
    messages = db.query(Message).filter(
        Message.conversation_id == chat_id
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages
