from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.authentication import requires
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, Message, GroupParticipant
from schemas import UserUpdate, UserDetailResponse
import uuid

async def get_users(request: Request):
    """Get all users"""
    try:
        async for db in get_db():
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            user_list = []
            for user in users:
                user_list.append({
                    "uuid": str(user.uuid),
                    "name": user.name,
                    "created_date": user.created_date.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                })
            
            return JSONResponse({"users": user_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get users: {str(e)}"}, 
            status_code=400
        )

async def get_user(request: Request):
    """Get a specific user by UUID"""
    try:
        user_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(select(User).where(User.uuid == user_uuid))
            user = result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    {"error": "User not found"}, 
                    status_code=404
                )
            
            return JSONResponse({
                "uuid": str(user.uuid),
                "name": user.name,
                "created_date": user.created_date.isoformat(),
                "updated_at": user.updated_at.isoformat()
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get user: {str(e)}"}, 
            status_code=400
        )

async def update_user(request: Request):
    """Update user information"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        body = await request.json()
        user_data = UserUpdate(**body)
        
        async for db in get_db():
            result = await db.execute(select(User).where(User.uuid == request.user.username))
            user = result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    {"error": "User not found"}, 
                    status_code=404
                )
            
            # Update user fields
            if user_data.name is not None:
                user.name = user_data.name
            
            await db.commit()
            await db.refresh(user)
            
            return JSONResponse({
                "message": "User updated successfully",
                "user": {
                    "uuid": str(user.uuid),
                    "name": user.name,
                    "created_date": user.created_date.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                }
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to update user: {str(e)}"}, 
            status_code=400
        )

async def delete_user(request: Request):
    """Delete a user (requires authentication)"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        async for db in get_db():
            result = await db.execute(select(User).where(User.uuid == request.user.username))
            user = result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    {"error": "User not found"}, 
                    status_code=404
                )
            
            # Delete user (cascade will handle related records)
            await db.delete(user)
            await db.commit()
            
            return JSONResponse({
                "message": "User deleted successfully"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to delete user: {str(e)}"}, 
            status_code=400
        )

async def get_user_messages(request: Request):
    """Get all messages sent by a user"""
    try:
        user_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(
                select(Message).where(
                    Message.sender_uuid == user_uuid,
                    Message.is_deleted == False
                ).order_by(Message.created_date.desc())
            )
            messages = result.scalars().all()
            
            message_list = []
            for message in messages:
                message_list.append({
                    "id": message.id,
                    "content": message.content,
                    "file": message.file,
                    "group_uuid": str(message.group_uuid),
                    "created_date": message.created_date.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                    "is_deleted": message.is_deleted
                })
            
            return JSONResponse({"messages": message_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get user messages: {str(e)}"}, 
            status_code=400
        )

async def get_user_groups(request: Request):
    """Get all groups a user is part of"""
    try:
        user_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(
                select(GroupParticipant).where(GroupParticipant.user_uuid == user_uuid)
            )
            participants = result.scalars().all()
            
            group_list = []
            for participant in participants:
                group_list.append({
                    "group_uuid": str(participant.group_uuid),
                    "joined_at": participant.joined_at.isoformat()
                })
            
            return JSONResponse({"groups": group_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get user groups: {str(e)}"}, 
            status_code=400
        )

# Route definitions
user_routes = [
    Route("/", get_users, methods=["GET"]),
    Route("/{uuid:uuid}", get_user, methods=["GET"]),
    Route("/me", update_user, methods=["PUT"]),
    Route("/me", delete_user, methods=["DELETE"]),
    Route("/{uuid:uuid}/messages", get_user_messages, methods=["GET"]),
    Route("/{uuid:uuid}/groups", get_user_groups, methods=["GET"]),
]
