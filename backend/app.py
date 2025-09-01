from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from database import engine, Base
from models import User, Group, Message, GroupParticipant
from routes import auth_routes, user_routes, group_routes, message_routes, stream_routes
from middleware import JWTAuthBackend

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

# Create Starlette app
app = Starlette(
    debug=True,
    lifespan=lifespan,
    routes=[
        Mount("/auth", routes=auth_routes),
        Mount("/users", routes=user_routes),
        Mount("/groups", routes=group_routes),
        Mount("/messages", routes=message_routes),
        Mount("/stream", routes=stream_routes),
        Route("/", endpoint=home),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
        Middleware(AuthenticationMiddleware, backend=JWTAuthBackend()),
    ]
)

async def home(request: Request):
    return JSONResponse({
        "message": "Chat Room API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "users": "/users", 
            "groups": "/groups",
            "messages": "/messages",
            "stream": "/stream"
        }
    })

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
