from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(25), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
    group_participants = relationship("GroupParticipant", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(uuid={self.uuid}, name='{self.name}')>"

class Group(Base):
    __tablename__ = "groups"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")
    participants = relationship("GroupParticipant", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(uuid={self.uuid})>"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_uuid = Column(UUID(as_uuid=True), ForeignKey("groups.uuid"), nullable=False)
    content = Column(Text, nullable=False)
    file = Column(String(500), nullable=True)  # Optional file path/URL
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    sender_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    
    # Indexes for fast lookup
    __table_args__ = (
        Index('idx_message_group', 'group_uuid'),
        Index('idx_message_sender', 'sender_uuid'),
        Index('idx_message_created', 'created_date'),
        Index('idx_message_group_created', 'group_uuid', 'created_date'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, content='{self.content[:50]}...', group={self.group_uuid})>"

class GroupParticipant(Base):
    __tablename__ = "group_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_uuid = Column(UUID(as_uuid=True), ForeignKey("groups.uuid"), nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="participants")
    user = relationship("User", back_populates="group_participants")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('group_uuid', 'user_uuid', name='uq_group_user'),
        Index('idx_participant_group', 'group_uuid'),
        Index('idx_participant_user', 'user_uuid'),
    )
    
    def __repr__(self):
        return f"<GroupParticipant(id={self.id}, group={self.group_uuid}, user={self.user_uuid})>"
