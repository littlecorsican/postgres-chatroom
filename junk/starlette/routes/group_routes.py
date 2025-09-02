from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.authentication import requires
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Group, User, Message, GroupParticipant
from schemas import GroupCreate
import uuid

async def create_group(request: Request):
    """Create a new group"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        body = await request.json()
        group_data = GroupCreate(**body)
        
        async for db in get_db():
            # Create new group
            new_group = Group(uuid=uuid.uuid4())
            db.add(new_group)
            await db.commit()
            await db.refresh(new_group)
            
            # Add creator as participant
            participant = GroupParticipant(
                group_uuid=new_group.uuid,
                user_uuid=uuid.UUID(request.user.username)
            )
            db.add(participant)
            await db.commit()
            
            return JSONResponse({
                "message": "Group created successfully",
                "group": {
                    "uuid": str(new_group.uuid),
                    "created_date": new_group.created_date.isoformat(),
                    "updated_at": new_group.updated_at.isoformat()
                }
            }, status_code=201)
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to create group: {str(e)}"}, 
            status_code=400
        )

async def get_groups(request: Request):
    """Get all groups"""
    try:
        async for db in get_db():
            result = await db.execute(select(Group))
            groups = result.scalars().all()
            
            group_list = []
            for group in groups:
                group_list.append({
                    "uuid": str(group.uuid),
                    "created_date": group.created_date.isoformat(),
                    "updated_at": group.updated_at.isoformat()
                })
            
            return JSONResponse({"groups": group_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get groups: {str(e)}"}, 
            status_code=400
        )

async def get_group(request: Request):
    """Get a specific group by UUID"""
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(select(Group).where(Group.uuid == group_uuid))
            group = result.scalar_one_or_none()
            
            if not group:
                return JSONResponse(
                    {"error": "Group not found"}, 
                    status_code=404
                )
            
            return JSONResponse({
                "uuid": str(group.uuid),
                "created_date": group.created_date.isoformat(),
                "updated_at": group.updated_at.isoformat()
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get group: {str(e)}"}, 
            status_code=400
        )

async def delete_group(request: Request):
    """Delete a group (requires authentication and ownership)"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            # Check if user is participant
            result = await db.execute(
                select(GroupParticipant).where(
                    GroupParticipant.group_uuid == group_uuid,
                    GroupParticipant.user_uuid == request.user.username
                )
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                return JSONResponse(
                    {"error": "Not a member of this group"}, 
                    status_code=403
                )
            
            # Get group
            result = await db.execute(select(Group).where(Group.uuid == group_uuid))
            group = result.scalar_one_or_none()
            
            if not group:
                return JSONResponse(
                    {"error": "Group not found"}, 
                    status_code=404
                )
            
            # Delete group (cascade will handle related records)
            await db.delete(group)
            await db.commit()
            
            return JSONResponse({
                "message": "Group deleted successfully"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to delete group: {str(e)}"}, 
            status_code=400
        )

async def join_group(request: Request):
    """Join a group"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            # Check if group exists
            result = await db.execute(select(Group).where(Group.uuid == group_uuid))
            group = result.scalar_one_or_none()
            
            if not group:
                return JSONResponse(
                    {"error": "Group not found"}, 
                    status_code=404
                )
            
            # Check if already a participant
            result = await db.execute(
                select(GroupParticipant).where(
                    GroupParticipant.group_uuid == group_uuid,
                    GroupParticipant.user_uuid == request.user.username
                )
            )
            existing_participant = result.scalar_one_or_none()
            
            if existing_participant:
                return JSONResponse(
                    {"error": "Already a member of this group"}, 
                    status_code=400
                )
            
            # Add participant
            participant = GroupParticipant(
                group_uuid=group_uuid,
                user_uuid=uuid.UUID(request.user.username)
            )
            db.add(participant)
            await db.commit()
            
            return JSONResponse({
                "message": "Successfully joined group"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to join group: {str(e)}"}, 
            status_code=400
        )

async def leave_group(request: Request):
    """Leave a group"""
    if not request.user.is_authenticated:
        return JSONResponse(
            {"error": "Not authenticated"}, 
            status_code=401
        )
    
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            # Remove participant
            result = await db.execute(
                select(GroupParticipant).where(
                    GroupParticipant.group_uuid == group_uuid,
                    GroupParticipant.user_uuid == request.user.username
                )
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                return JSONResponse(
                    {"error": "Not a member of this group"}, 
                    status_code=400
                )
            
            await db.delete(participant)
            await db.commit()
            
            return JSONResponse({
                "message": "Successfully left group"
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to leave group: {str(e)}"}, 
            status_code=400
        )

async def get_group_participants(request: Request):
    """Get all participants of a group"""
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(
                select(GroupParticipant).where(GroupParticipant.group_uuid == group_uuid)
            )
            participants = result.scalars().all()
            
            participant_list = []
            for participant in participants:
                # Get user details
                user_result = await db.execute(
                    select(User).where(User.uuid == participant.user_uuid)
                )
                user = user_result.scalar_one_or_none()
                
                if user:
                    participant_list.append({
                        "user_uuid": str(participant.user_uuid),
                        "user_name": user.name,
                        "joined_at": participant.joined_at.isoformat()
                    })
            
            return JSONResponse({"participants": participant_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get group participants: {str(e)}"}, 
            status_code=400
        )

async def get_group_messages(request: Request):
    """Get all messages in a group"""
    try:
        group_uuid = request.path_params["uuid"]
        
        async for db in get_db():
            result = await db.execute(
                select(Message).where(
                    Message.group_uuid == group_uuid,
                    Message.is_deleted == False
                ).order_by(Message.created_date.desc())
            )
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
                    "sender_uuid": str(message.sender_uuid),
                    "sender_name": user.name if user else "Unknown",
                    "created_date": message.created_date.isoformat(),
                    "updated_at": message.updated_at.isoformat(),
                    "is_deleted": message.is_deleted
                })
            
            return JSONResponse({"messages": message_list})
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to get group messages: {str(e)}"}, 
            status_code=400
        )

# Route definitions
group_routes = [
    Route("/", create_group, methods=["POST"]),
    Route("/", get_groups, methods=["GET"]),
    Route("/{uuid:uuid}", get_group, methods=["GET"]),
    Route("/{uuid:uuid}", delete_group, methods=["DELETE"]),
    Route("/{uuid:uuid}/join", join_group, methods=["POST"]),
    Route("/{uuid:uuid}/leave", leave_group, methods=["POST"]),
    Route("/{uuid:uuid}/participants", get_group_participants, methods=["GET"]),
    Route("/{uuid:uuid}/messages", get_group_messages, methods=["GET"]),
]
