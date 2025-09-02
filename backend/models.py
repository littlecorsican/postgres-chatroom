from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    file: Optional[str] = Field(None, max_length=50)
    sender_id: uuid.UUID

class MessageResponse(BaseModel):
    id: int
    content: str
    file: Optional[str]
    created_date: datetime
    sender_id: uuid.UUID
    
    class Config:
        from_attributes = True

class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    next_cursor: Optional[str] = None
    has_more: bool

class PaginationParams(BaseModel):
    cursor: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
