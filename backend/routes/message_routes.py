from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.authentication import requires
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Message, User, Group, GroupParticipant
from schemas import MessageCreate, MessageUpdate
from redis_client import redis_client
import uuid
import json

async def create_message(request: Request):
    """Create a new message in a group"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        body = await request.json()
        message_data = MessageCreate(**body)
        
        async for db in get_db():
            # Check if user is participant of the group
            result = await db.execute(
                select(GroupParticipant).where(
                    GroupParticipant.group_uuid == message_data.group_uuid,
                    GroupParticipant.user_uuid == request.user.username
                )
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                return JSONResponse(
                    {"error": "Not a member of this group"}, 
                    status_code=403
                )
            
            # Create new message
            new_message = Message(
                group_uuid=message_data.group_uuid,
                content=message_data.content,
                file=message_data.file,
                sender_uuid=uuid.UUID(request.user.username)
            )
            
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            
            # Publish message to Redis for real-time updates
            message_data = {
                "id": new_message.id,
                "content": new_message.content,
                "file": new_message.file,
                "group_uuid": str(new_message.group_uuid),
                "sender_uuid": str(new_message.sender_uuid),
                "sender_name": user.name if user else "Unknown",
                "created_date": new_message.created_date.isoformat(),
                "updated_at": new_message.updated_at.isoformat(),
                "is_deleted": new_message.is_deleted
            }
            
            # Publish to group-specific channel
            group_channel = f"group:{message_data['group_uuid']}"
            await redis_client.publish_json(group_channel, {
                "type": "new_message",
                "data": message_data
            })
            
            # Cache message in Redis for quick access
            message_key = f"message:{new_message.id}"
            await redis_client.set_json(message_key, message_data, ex=3600)  # 1 hour cache
            
            return JSONResponse({
                "message": "Message sent successfully",
                "data": message_data
            }, status_code=201)
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to send message: {str(e)}"}, 
            status_code=400
        )

async def get_messages(request: Request):
    """Get all messages with pagination and filtering"""
    try:
        async for db in get_db():
            # Get query parameters
            group_uuid = request.query_params.get("group_uuid")
            sender_uuid = request.query_params.get("sender_uuid")
            page = int(request.query_params.get("page", 1))
            per_page = int(request.query_params.get("per_page", 20))
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 100:
                per_page = 20
            
            offset = (page - 1) * per_page
            
            # Build query
            query = select(Message).where(Message.is_deleted == False)
            
            if group_uuid:
                query = query.where(Message.group_uuid == group_uuid)
            if sender_uuid:
                query = query.where(Message.sender_uuid == sender_uuid)
            
            # Get total count for pagination
            count_query = select(func.count(Message.id)).where(Message.is_deleted == False)
            if group_uuid:
                count_query = count_query.where(Message.group_uuid == group_uuid)
            if sender_uuid:
                count_query = count_query.where(Message.sender_uuid == sender_uuid)
            
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # Get messages with pagination
            query = query.order_by(Message.created_date.desc()).limit(per_page).offset(offset)
            result = await db.execute(query)
            messages = result.scalars().all()
            
            message_list = []
            for message in messages:
                # Get sender details
                user_result = await db.execute(
                    select(User).where(User.uuid == message.sender_uuid)
                )
                user = user_result.scalar_one_or_none()
                
                message_list.append({
                    "id": message.id,
                    "content": message.content,
                    "file": message.file,
                    "group_uuid": str(message.group_uuid),
                    "sender_uuid": str(message.sender_uuid),
                    "sender_name": user.name if user else "Unknown",
                    "created_date": message.created_date.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                    "is_deleted": message.is_deleted
                })
            
            # Calculate pagination info
            total_pages = (total_count + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            return JSONResponse({
                "messages": message_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev,
                    "next_page": page + 1 if has_next else None,
                    "prev_page": page - 1 if has_prev else None
                }
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get messages: {str(e)}"}, 
            status_code=400
        )

async def get_message(request: Request):
    """Get a specific message by ID"""
    try:
        message_id = int(request.path_params["id"])
        
        async for db in get_db():
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            
            if not message:
                return JSONResponse(
                    {"error": "Message not found"}, 
                    status_code=404
                )
            
            if message.is_deleted:
                return JSONResponse(
                    {"error": "Message has been deleted"}, 
                    status_code=404
                )
            
            # Get sender details
            user_result = await db.execute(
                select(User).where(User.uuid == message.sender_uuid)
            )
            user = user_result.scalar_one_or_none()
            
            return JSONResponse({
                "id": message.id,
                "content": message.content,
                "file": message.file,
                "group_uuid": str(message.group_uuid),
                "sender_uuid": str(message.sender_uuid),
                "sender_name": user.name if user else "Unknown",
                "created_date": message.created_date.isoformat(),
                "updated_at": message.updated_at.isoformat(),
                "is_deleted": message.is_deleted
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get message: {str(e)}"}, 
            status_code=400
        )

async def update_message(request: Request):
    """Update a message (only by sender)"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        message_id = int(request.path_params["id"])
        body = await request.json()
        message_data = MessageUpdate(**body)
        
        async for db in get_db():
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            
            if not message:
                return JSONResponse(
                    {"error": "Message not found"}, 
                    status_code=404
                )
            
            if message.is_deleted:
                return JSONResponse(
                    {"error": "Cannot update deleted message"}, 
                    status_code=400
                )
            
            # Check if user is the sender
            if str(message.sender_uuid) != request.user.username:
                return JSONResponse(
                    {"error": "Can only edit your own messages"}, 
                    status_code=403
                )
            
            # Update message fields
            if message_data.content is not None:
                message.content = message_data.content
            if message_data.file is not None:
                message.file = message_data.file
            
            await db.commit()
            await db.refresh(message)
            
            return JSONResponse({
                "message": "Message updated successfully",
                "data": {
                    "id": message.id,
                    "content": message.content,
                    "file": message.file,
                    "group_uuid": str(message.group_uuid),
                    "sender_uuid": str(message.sender_uuid),
                    "created_date": message.created_date.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                    "is_deleted": message.is_deleted
                }
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to update message: {str(e)}"}, 
            status_code=400
        )

async def delete_message(request: Request):
    """Soft delete a message (only by sender)"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        message_id = int(request.path_params["id"])
        
        async for db in get_db():
            result = await db.execute(select(Message).where(Message.id == message_id))
            message = result.scalar_one_or_none()
            
            if not message:
                return JSONResponse(
                    {"error": "Message not found"}, 
                    status_code=404
                )
            
            if message.is_deleted:
                return JSONResponse(
                    {"error": "Message already deleted"}, 
                    status_code=400
                )
            
            # Check if user is the sender
            if str(message.sender_uuid) != request.user.username:
                return JSONResponse(
                    {"error": "Can only delete your own messages"}, 
                    status_code=403
                )
            
            # Soft delete
            message.is_deleted = True
            await db.commit()
            
            return JSONResponse({
                "message": "Message deleted successfully"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to delete message: {str(e)}"}, 
            status_code=400
        )

async def search_messages(request: Request):
    """Search messages by content"""
    try:
        query = request.query_params.get("q", "")
        if not query:
            return JSONResponse(
                {"error": "Search query is required"}, 
                status_code=400
            )
        
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))
        
        async for db in get_db():
            # Search in message content
            result = await db.execute(
                select(Message).where(
                    Message.content.ilike(f"%{query}%"),
                    Message.is_deleted == False
                ).order_by(Message.created_date.desc()).limit(limit).offset(offset)
            )
            messages = result.scalars().all()
            
            message_list = []
            for message in messages:
                # Get sender details
                user_result = await db.execute(
                    select(User).where(User.uuid == message.sender_uuid)
                )
                user = user_result.scalar_one_or_none()
                
                # Get group details
                group_result = await db.execute(
                    select(Group).where(Group.uuid == message.group_uuid)
                )
                group = group_result.scalar_one_or_none()
                
                message_list.append({
                    "id": message.id,
                    "content": message.content,
                    "file": message.file,
                    "group_uuid": str(message.group_uuid),
                    "sender_uuid": str(message.sender_uuid),
                    "sender_name": user.name if user else "Unknown",
                    "created_date": message.created_date.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                    "is_deleted": message.is_deleted
                })
            
            return JSONResponse({
                "query": query,
                "results": message_list,
                "total": len(message_list)
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Search failed: {str(e)}"}, 
            status_code=400
        )

# Route definitions
message_routes = [
    Route("/", create_message, methods=["POST"]),
    Route("/", get_messages, methods=["GET"]),
    Route("/search", search_messages, methods=["GET"]),
    Route("/{id:int}", get_message, methods=["GET"]),
    Route("/{id:int}", update_message, methods=["PUT"]),
    Route("/{id:int}", delete_message, methods=["DELETE"]),
]
