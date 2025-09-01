from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Base schemas
class UserBase(BaseModel):
    name: str = Field(..., max_length=25)

class GroupBase(BaseModel):
    pass

class MessageBase(BaseModel):
    content: str
    file: Optional[str] = None

class GroupParticipantBase(BaseModel):
    group_uuid: UUID
    user_uuid: UUID

# Create schemas
class UserCreate(UserBase):
    pass

class GroupCreate(GroupBase):
    pass

class MessageCreate(MessageBase):
    group_uuid: UUID

class GroupParticipantCreate(GroupParticipantBase):
    pass

# Update schemas
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=25)

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    file: Optional[str] = None

# Response schemas
class UserResponse(UserBase):
    uuid: UUID
    created_date: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupResponse(GroupBase):
    uuid: UUID
    created_date: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(MessageBase):
    id: int
    group_uuid: UUID
    created_date: datetime
    updated_at: datetime
    is_deleted: bool
    sender_uuid: UUID
    
    class Config:
        from_attributes = True

class GroupParticipantResponse(GroupParticipantBase):
    id: int
    joined_at: datetime
    
    class Config:
        from_attributes = True

# Detailed response schemas with relationships
class UserDetailResponse(UserResponse):
    messages: List[MessageResponse] = []
    groups: List[GroupResponse] = []

class GroupDetailResponse(GroupResponse):
    messages: List[MessageResponse] = []
    participants: List[UserResponse] = []

class MessageDetailResponse(MessageResponse):
    sender: UserResponse
    group: GroupResponse

# Auth schemas
class UserLogin(BaseModel):
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
