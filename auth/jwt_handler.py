"""
auth/jwt_handler.py - JWT token creation and verification
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from database.connection import get_database

# HTTP Bearer token scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.
    
    Args:
        data: Payload to encode (should include 'sub' = user_id)
        expires_delta: Custom expiry duration
    
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Raises:
        HTTPException 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    FastAPI dependency: extract and validate the current user from JWT.
    
    Usage:
        @router.get("/protected")
        async def protected(user = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = get_database()
    from bson import ObjectId

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Return a clean dict (no password)
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "school": user.get("school"),
        "subject": user.get("subject"),
    }
