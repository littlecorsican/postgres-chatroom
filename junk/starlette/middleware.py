from starlette.authentication import AuthenticationBackend, AuthenticationError, SimpleUser
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class JWTAuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request) -> Optional[tuple]:
        if "authorization" not in request.headers:
            return None
        
        try:
            scheme, token = request.headers["authorization"].split()
            if scheme.lower() != "bearer":
                return None
            
            # Decode JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_uuid: str = payload.get("sub")
            if user_uuid is None:
                raise AuthenticationError("Invalid token")
            
            # Create a simple user object
            user = SimpleUser(user_uuid)
            return (user, token)
            
        except (ValueError, JWTError):
            raise AuthenticationError("Invalid token")

def create_access_token(data: dict):
    """Create a JWT access token"""
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
