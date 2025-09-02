from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.authentication import requires
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import GroupParticipant
from redis_client import redis_client
import json
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def stream_messages(request: Request):
    """SSE endpoint for real-time message streaming"""
    if not request.user.is_authenticated:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Not authenticated'})}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    try:
        # Get group UUID from query params
        group_uuid = request.query_params.get("group_uuid")
        if not group_uuid:
            return StreamingResponse(
                iter([f"data: {json.dumps({'error': 'group_uuid parameter required'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        # Verify user is member of the group
        async for db in get_db():
            result = await db.execute(
                select(GroupParticipant).where(
                    GroupParticipant.group_uuid == group_uuid,
                    GroupParticipant.user_uuid == request.user.username
                )
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                return StreamingResponse(
                    iter([f"data: {json.dumps({'error': 'Not a member of this group'})}\n\n"]),
                    media_type="text/event-stream"
                )
        
        # Subscribe to group channel
        group_channel = f"group:{group_uuid}"
        await redis_client.subscribe(group_channel)
        
        async def event_generator():
            """Generate SSE events"""
            try:
                # Send initial connection message
                yield f"data: {json.dumps({'type': 'connected', 'group_uuid': group_uuid})}\n\n"
                
                # Listen for messages
                async for message in redis_client.listen():
                    if message["type"] == "message":
                        try:
                            # Parse the message data
                            data = json.loads(message["data"])
                            
                            # Send as SSE event
                            sse_data = json.dumps(data)
                            yield f"data: {sse_data}\n\n"
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse Redis message: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {e}")
                            continue
                            
            except asyncio.CancelledError:
                logger.info("SSE connection cancelled")
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                yield f"data: {json.dumps({'error': 'Stream error occurred'})}\n\n"
            finally:
                # Cleanup: unsubscribe from channel
                try:
                    await redis_client.unsubscribe(group_channel)
                except Exception as e:
                    logger.error(f"Error unsubscribing from channel: {e}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to establish SSE stream: {e}")
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': f'Failed to establish stream: {str(e)}'})}\n\n"]),
            media_type="text/event-stream"
        )

async def stream_all_messages(request: Request):
    """SSE endpoint for streaming all messages across groups user is member of"""
    if not request.user.is_authenticated:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'Not authenticated'})}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    try:
        # Get all groups user is member of
        async for db in get_db():
            result = await db.execute(
                select(GroupParticipant).where(GroupParticipant.user_uuid == request.user.username)
            )
            participants = result.scalars().all()
            
            if not participants:
                return StreamingResponse(
                    iter([f"data: {json.dumps({'error': 'User is not a member of any groups'})}\n\n"]),
                    media_type="text/event-stream"
                )
        
        # Subscribe to all group channels
        group_channels = [f"group:{participant.group_uuid}" for participant in participants]
        
        for channel in group_channels:
            await redis_client.subscribe(channel)
        
        async def event_generator():
            """Generate SSE events for all groups"""
            try:
                # Send initial connection message
                yield f"data: {json.dumps({'type': 'connected', 'groups': [str(p.group_uuid) for p in participants]})}\n\n"
                
                # Listen for messages from all channels
                async for message in redis_client.listen():
                    if message["type"] == "message":
                        try:
                            # Parse the message data
                            data = json.loads(message["data"])
                            
                            # Send as SSE event
                            sse_data = json.dumps(data)
                            yield f"data: {sse_data}\n\n"
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse Redis message: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing Redis message: {e}")
                            continue
                            
            except asyncio.CancelledError:
                logger.info("SSE connection cancelled")
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                yield f"data: {json.dumps({'error': 'Stream error occurred'})}\n\n"
            finally:
                # Cleanup: unsubscribe from all channels
                for channel in group_channels:
                    try:
                        await redis_client.unsubscribe(channel)
                    except Exception as e:
                        logger.error(f"Error unsubscribing from channel {channel}: {e}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to establish SSE stream: {e}")
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': f'Failed to establish stream: {str(e)}'})}\n\n"]),
            media_type="text/event-stream"
        )

async def health_check(request: Request):
    """Health check endpoint for Redis connection"""
    try:
        # Test Redis connection
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": str(e)}

# Route definitions
stream_routes = [
    Route("/group", stream_messages, methods=["GET"]),
    Route("/all", stream_all_messages, methods=["GET"]),
    Route("/health", health_check, methods=["GET"]),
]
