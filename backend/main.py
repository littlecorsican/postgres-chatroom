from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, StreamingResponse
from starlette.requests import Request
from starlette.websockets import WebSocket
from starlette.background import BackgroundTask
import json
import asyncio
from datetime import datetime
import uuid
from typing import Optional

from database import get_db, init_db, Message
from redis_client import redis_client
from postgres_listener import postgres_listener
from models import MessageCreate, MessageResponse, MessageListResponse, PaginationParams
from config import Config

# Initialize Redis connection
async def startup():
    await redis_client.connect()
    await init_db()
    # Start PostgreSQL listener in background
    asyncio.create_task(postgres_listener.start())

async def shutdown():
    await redis_client.disconnect()
    await postgres_listener.stop()

# Create Starlette app
app = Starlette(
    debug=Config.DEBUG,
    on_startup=[startup],
    on_shutdown=[shutdown],
    routes=[
        Route("/message", message_endpoint, methods=["GET", "POST"]),
        Route("/stream", stream_endpoint),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]
)

async def message_endpoint(request: Request):
    """Handle GET and POST requests for messages"""
    if request.method == "GET":
        return await get_messages(request)
    elif request.method == "POST":
        return await create_message(request)

async def get_messages(request: Request):
    """Get paginated messages using cursor pagination"""
    try:
        # Parse query parameters
        cursor = request.query_params.get("cursor")
        limit = int(request.query_params.get("limit", Config.DEFAULT_PAGE_SIZE))
        limit = min(limit, Config.MAX_PAGE_SIZE)
        
        async with get_db() as db:
            # Build query
            query = db.query(Message).order_by(Message.created_date.desc())
            
            if cursor:
                try:
                    # Decode cursor (timestamp in ISO format)
                    cursor_date = datetime.fromisoformat(cursor)
                    query = query.filter(Message.created_date < cursor_date)
                except ValueError:
                    return JSONResponse({"error": "Invalid cursor format"}, status_code=400)
            
            # Get messages with limit + 1 to check if there are more
            messages = await db.execute(query.limit(limit + 1))
            message_list = messages.scalars().all()
            
            # Check if there are more messages
            has_more = len(message_list) > limit
            if has_more:
                message_list = message_list[:-1]  # Remove the extra message
            
            # Create response
            message_responses = [
                MessageResponse(
                    id=msg.id,
                    content=msg.content,
                    file=msg.file,
                    created_date=msg.created_date,
                    sender_id=msg.sender_id
                ) for msg in message_list
            ]
            
            # Create next cursor
            next_cursor = None
            if message_list and has_more:
                next_cursor = message_list[-1].created_date.isoformat()
            
            response = MessageListResponse(
                messages=message_responses,
                next_cursor=next_cursor,
                has_more=has_more
            )
            
            return JSONResponse(response.dict())
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def create_message(request: Request):
    """Create a new message"""
    try:
        # Parse request body
        body = await request.json()
        message_data = MessageCreate(**body)
        
        async with get_db() as db:
            # Create new message
            new_message = Message(
                content=message_data.content,
                file=message_data.file,
                sender_id=message_data.sender_id
            )
            
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            
            # Create response
            response = MessageResponse(
                id=new_message.id,
                content=new_message.content,
                file=new_message.file,
                created_date=new_message.created_date,
                sender_id=new_message.sender_id
            )
            
            return JSONResponse(response.dict(), status_code=201)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def stream_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time message streaming"""
    
    async def event_stream():
        """Generate SSE events"""
        try:
            # Subscribe to Redis channel for new messages
            pubsub = await redis_client.subscribe('new_messages')
            
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to message stream'})}\n\n"
            
            # Listen for new messages
            async for message in redis_client.listen():
                try:
                    data = json.loads(message)
                    yield f"data: {json.dumps({'type': 'new_message', 'data': data})}\n\n"
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            if redis_client.pubsub:
                await redis_client.pubsub.unsubscribe('new_messages')
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info"
    )
