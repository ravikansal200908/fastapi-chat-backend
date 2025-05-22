from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Dict, Annotated
from uuid import UUID
from datetime import datetime
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.auth import get_current_user
from app.db.postgres import get_db
from app.db.mongodb import get_mongodb
from app.models.models import User, ChatRecord, Conversation
from app.schemas.schemas import BranchCreate, Branch as BranchSchema
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/create-branch", response_model=BranchSchema, status_code=status.HTTP_201_CREATED)
async def create_branch(
    *,
    db: Annotated[Session, Depends(get_db)],
    mongodb: Annotated[AsyncIOMotorDatabase, Depends(get_mongodb)],
    branch_in: BranchCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new branch from a specific message.
    
    Parameters:
    - branch_in: BranchCreate object containing:
        - parent_chat_id: UUID of the parent chat
        - message_id: UUID of the message to branch from
    
    Returns:
    - Created branch record
    
    Raises:
    - HTTPException(404): If parent chat or message not found
    - HTTPException(403): If user doesn't have access to the parent chat
    """
    # Verify parent chat exists and belongs to user
    parent_chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == branch_in.parent_chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not parent_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent chat not found"
        )
    
    # Create new chat record for branch
    branch_chat = ChatRecord(
        account_id=str(current_user.id),
        chat_type=parent_chat.chat_type,
        name=f"Branch from {parent_chat.name}",
        active=False
    )
    db.add(branch_chat)
    db.flush()
    
    # Create conversation for branch
    branch_conversation = Conversation(
        chat_id=branch_chat.chat_id,
        account_id=str(current_user.id),
        name=branch_chat.name,
        deleted=False
    )
    db.add(branch_conversation)
    
    # Create MongoDB document for branch
    branch_content = {
        "chat_id": str(branch_chat.chat_id),
        "parent_chat_id": str(branch_in.parent_chat_id),
        "parent_message_id": str(branch_in.message_id),
        "qa_pairs": []
    }
    await mongodb.chat_contents.insert_one(branch_content)
    
    # Update parent chat's MongoDB document
    await mongodb.chat_contents.update_one(
        {"chat_id": str(branch_in.parent_chat_id)},
        {"$push": {"qa_pairs.$[elem].branches": str(branch_chat.chat_id)}},
        array_filters=[{"elem.response_id": str(branch_in.message_id)}]
    )
    
    db.commit()
    db.refresh(branch_chat)
    return branch_chat

@router.get("/get-branches/{chat_id}", response_model=List[BranchSchema])
@cache(expire=300)  # Cache for 5 minutes
async def get_branches(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    chat_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all branches for a chat.
    
    Parameters:
    - chat_id: UUID of the parent chat
    
    Returns:
    - List of branch records
    
    Raises:
    - HTTPException(404): If parent chat not found
    - HTTPException(403): If user doesn't have access to the parent chat
    """
    # Verify parent chat exists and belongs to user
    parent_chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not parent_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent chat not found"
        )
    
    # Get all branches from MongoDB
    chat_content = await mongodb.chat_contents.find_one({"chat_id": str(chat_id)})
    if not chat_content:
        return []
    
    # Get branch details from PostgreSQL
    branch_ids = []
    for qa_pair in chat_content.get("qa_pairs", []):
        branch_ids.extend(qa_pair.get("branches", []))
    
    branches = db.query(ChatRecord).filter(
        ChatRecord.chat_id.in_(branch_ids)
    ).all()
    
    return branches

@router.get("/set-active-branch/{branch_id}", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def set_active_branch(
    *,
    db: Session = Depends(get_db),
    branch_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Set a specific branch as active.
    
    Parameters:
    - branch_id: UUID of the branch to activate
    
    Returns:
    - Updated branch record
    
    Raises:
    - HTTPException(404): If branch not found
    - HTTPException(403): If user doesn't have access to the branch
    """
    branch = db.query(ChatRecord).filter(
        ChatRecord.chat_id == branch_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    branch.active = True
    db.commit()
    db.refresh(branch)
    
    return {
        "name": branch.name,
        "chat_type": branch.chat_type,
        "active": branch.active,
        "chat_id": str(branch.chat_id),
        "account_id": branch.account_id,
        "created_at": branch.created_at.isoformat(),
        "updated_at": branch.updated_at.isoformat()
    }

@router.get("/get-branch-tree/{chat_id}", response_class=JSONResponse)
@cache(expire=300)  # Cache for 5 minutes
async def get_branch_tree(
    *,
    db: Session = Depends(get_db),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    chat_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a complete tree of all branches for a chat.
    
    Parameters:
    - chat_id: UUID of the parent chat
    
    Returns:
    - Tree structure of all branches with their relationships
    
    Raises:
    - HTTPException(404): If parent chat not found
    - HTTPException(403): If user doesn't have access to the parent chat
    """
    # Verify parent chat exists and belongs to user
    parent_chat = db.query(ChatRecord).filter(
        ChatRecord.chat_id == chat_id,
        ChatRecord.account_id == str(current_user.id)
    ).first()
    
    if not parent_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent chat not found"
        )
    
    # Get all chat contents from MongoDB
    chat_contents = await mongodb.chat_contents.find(
        {"$or": [
            {"chat_id": str(chat_id)},
            {"parent_chat_id": str(chat_id)}
        ]}
    ).to_list(length=None)
    
    # Create a map of chat_id to content
    content_map = {content["chat_id"]: content for content in chat_contents}
    
    # Get all branches from PostgreSQL
    branch_ids = set()
    for content in chat_contents:
        branch_ids.add(content["chat_id"])
        if "parent_chat_id" in content:
            branch_ids.add(content["parent_chat_id"])
    
    branches = db.query(ChatRecord).filter(
        ChatRecord.chat_id.in_(branch_ids)
    ).all()
    
    # Create a map of chat_id to branch
    branch_map = {str(branch.chat_id): branch for branch in branches}
    
    # Build the tree structure
    def build_tree(chat_id: str) -> Dict:
        content = content_map.get(chat_id, {})
        branch = branch_map.get(chat_id)
        
        if not branch:
            return None
        
        node = {
            "chat_id": str(branch.chat_id),
            "name": branch.name,
            "active": branch.active,
            "chat_type": branch.chat_type,
            "created_at": branch.created_at.isoformat(),
            "updated_at": branch.updated_at.isoformat(),
            "children": []
        }
        
        # Add message info if available
        if "parent_message_id" in content:
            node["parent_message_id"] = content["parent_message_id"]
        
        # Find all child branches
        for other_content in chat_contents:
            if other_content.get("parent_chat_id") == chat_id:
                child = build_tree(other_content["chat_id"])
                if child:
                    node["children"].append(child)
        
        return node
    
    # Start building from the root
    tree = build_tree(str(chat_id))
    
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch tree not found"
        )
    
    return tree 