from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.auth import get_current_user, get_password_hash
from app.db.postgres import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, User as UserSchema, UserUpdate
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Create a new user.
    
    Parameters:
    - user_in: UserCreate object containing:
        - username: Username for the new user
        - email: Email address for the new user
        - password: Plain text password
    
    Returns:
    - Created user object
    
    Raises:
    - HTTPException(400): If username or email already exists
    """
    # Check if username exists
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserSchema)
@cache(expire=300)  # Cache for 5 minutes
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    
    Returns:
    - User object
    
    Raises:
    - HTTPException(401): If user is not authenticated
    """
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_current_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update current user information.
    
    Parameters:
    - user_in: UserCreate object containing updated user data
    
    Returns:
    - Updated user object
    
    Raises:
    - HTTPException(401): If user is not authenticated
    - HTTPException(400): If update fails
    """
    # Update user fields
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific user by ID.
    
    Parameters:
    - user_id: UUID of the user to retrieve
    
    Returns:
    - User object
    
    Raises:
    - HTTPException(404): If user not found
    - HTTPException(401): If user is not authenticated
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user 