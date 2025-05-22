from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.postgres import Base

class ChatType(str, enum.Enum):
    """Enum for chat types."""
    DIRECT = "DIRECT"
    GROUP = "GROUP"
    CHANNEL = "CHANNEL"

class ChatRecord(Base):
    __tablename__ = "chat_records"

    chat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False)
    chat_type = Column(SQLEnum(ChatType), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="chat_record", uselist=False, cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat_records.chat_id"), primary_key=True)
    account_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    deleted = Column(Boolean, default=False)

    # Relationships
    chat_record = relationship("ChatRecord", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.chat_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages") 