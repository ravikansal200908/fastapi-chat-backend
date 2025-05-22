from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.auth import get_current_user
from app.db.postgres import get_db
from app.models.models import User, Conversation
from app.schemas.schemas import ConversationCreate, Conversation as ConversationSchema
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/", response_model=ConversationSchema, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new conversation.
    
    Parameters:
    - conversation_in: ConversationCreate object containing:
        - chat_id: UUID of the parent chat
        - name: Name of the conversation
    
    Returns:
    - Created conversation object
    
    Raises:
    - HTTPException(404): If parent chat not found
    - HTTPException(403): If user doesn't have access to the parent chat
    """
    conversation = Conversation(
        chat_id=conversation_in.chat_id,
        account_id=str(current_user.id),
        name=conversation_in.name,
        deleted=False
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    # Invalidate cache for conversations list
    await FastAPICache.clear(namespace="conversations")
    
    return conversation

@router.get("/", response_model=List[ConversationSchema])
@cache(expire=300, namespace="conversations")  # Cache for 5 minutes
async def get_conversations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all conversations for the current user with pagination.
    
    Parameters:
    - skip: Number of conversations to skip (for pagination)
    - limit: Maximum number of conversations to return
    
    Returns:
    - List of conversation objects
    
    Raises:
    - HTTPException(401): If user is not authenticated
    """
    conversations = db.query(Conversation).filter(
        Conversation.account_id == str(current_user.id),
        Conversation.deleted == False
    ).offset(skip).limit(limit).all()
    return conversations

@router.get("/{conversation_id}", response_model=ConversationSchema)
@cache(expire=300)  # Cache for 5 minutes
async def get_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific conversation by ID.
    
    Parameters:
    - conversation_id: UUID of the conversation
    
    Returns:
    - Conversation object
    
    Raises:
    - HTTPException(404): If conversation not found
    - HTTPException(403): If user doesn't have access to the conversation
    """
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == conversation_id,
        Conversation.account_id == str(current_user.id),
        Conversation.deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.delete("/{conversation_id}", response_model=dict)
async def delete_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Soft delete a conversation.
    
    Parameters:
    - conversation_id: UUID of the conversation to delete
    
    Returns:
    - Success message
    
    Raises:
    - HTTPException(404): If conversation not found
    - HTTPException(403): If user doesn't have access to the conversation
    """
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == conversation_id,
        Conversation.account_id == str(current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation.deleted = True
    db.commit()
    
    return {
        "status": "success",
        "message": f"Conversation {conversation_id} has been successfully deleted"
    }

@router.get("/{conversation_id}/branches", response_model=List[ConversationSchema])
def get_conversation_branches(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all branches of a specific conversation.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    branches = db.query(Conversation).filter(
        Conversation.parent_conversation_id == conversation_id
    ).all()
    return branches 