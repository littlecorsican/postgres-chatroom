from sqlalchemy import Column, Integer, Text, String, DateTime, UUID, Index
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from config import Config

# Create async engine
engine = create_async_engine(Config.DATABASE_URL, echo=Config.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    file = Column(String(50), nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sender_id = Column(UUID, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Message(id={self.id}, content='{self.content[:50]}...', sender_id={self.sender_id})>"

# Create indexes
Index('idx_messages_created_date', Message.created_date)
Index('idx_messages_sender_id', Message.sender_id)

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
