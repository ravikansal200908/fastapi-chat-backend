from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, validator, UUID4
from enum import Enum

class ChatType(str, Enum):
    DIRECT = "DIRECT"
    GROUP = "GROUP"
    CHANNEL = "CHANNEL"

class ChatRecordBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    chat_type: ChatType
    active: bool = True

class ChatRecordCreate(ChatRecordBase):
    pass

class ChatRecordUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    active: Optional[bool] = None

class ChatRecord(ChatRecordBase):
    chat_id: UUID4
    account_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ConversationCreate(ConversationBase):
    chat_id: UUID4

class Conversation(ConversationBase):
    chat_id: UUID4
    account_id: str
    deleted: bool

    class Config:
        from_attributes = True

class QAPair(BaseModel):
    question: str
    response: str
    response_id: str
    timestamp: datetime
    branches: List[str] = []

class ChatContent(BaseModel):
    chat_id: str
    qa_pairs: List[QAPair] = []

class ChatContentCreate(ChatContent):
    pass

class ChatContent(ChatContent):
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class User(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)

class MessageCreate(MessageBase):
    conversation_id: UUID4

class Message(MessageBase):
    id: UUID4
    conversation_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str
    status_code: int = 200

class BranchCreate(BaseModel):
    parent_chat_id: UUID4
    message_id: UUID4

class Branch(ChatRecord):
    pass

class BranchActiveUpdate(BaseModel):
    active: bool = True 