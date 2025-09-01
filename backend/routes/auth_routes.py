from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.authentication import requires
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, TokenResponse
from middleware import create_access_token
import uuid

async def register(request: Request):
    """Register a new user"""
    try:
        body = await request.json()
        user_data = UserCreate(**body)
        
        async for db in get_db():
            # Check if user already exists
            result = await db.execute(select(User).where(User.name == user_data.name))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                return JSONResponse(
                    {"error": "User with this name already exists"}, 
                    status_code=400
                )
            
            # Create new user
            new_user = User(
                uuid=uuid.uuid4(),
                name=user_data.name
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # Create access token
            access_token = create_access_token(data={"sub": str(new_user.uuid)})
            
            return JSONResponse({
                "message": "User created successfully",
                "access_token": access_token,
                "user": {
                    "uuid": str(new_user.uuid),
                    "name": new_user.name,
                    "created_date": new_user.created_date.isoformat(),
                    "updated_at": new_user.updated_at.isoformat()
                }
            }, status_code=201)
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Registration failed: {str(e)}"}, 
            status_code=400
        )

async def login(request: Request):
    """Login user and return access token"""
    try:
        body = await request.json()
        login_data = UserLogin(**body)
        
        async for db in get_db():
            # Find user by name
            result = await db.execute(select(User).where(User.name == login_data.name))
            user = result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    {"error": "User not found"}, 
                    status_code=404
                )
            
            # Create access token
            access_token = create_access_token(data={"sub": str(user.uuid)})
            
            return JSONResponse({
                "message": "Login successful",
                "access_token": access_token,
                "user": {
                    "uuid": str(user.uuid),
                    "name": user.name,
                    "created_date": user.created_date.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                }
            })
            
    except Exception as e:
        return JSONResponse(
            {"error": f"Login failed: {str(e)}"}, 
            status_code=400
        )

async def get_current_user(request: Request):
    """Get current authenticated user"""
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

# Route definitions
auth_routes = [
    Route("/register", register, methods=["POST"]),
    Route("/login", login, methods=["POST"]),
    Route("/me", get_current_user, methods=["GET"]),
]
