"""
api/auth.py - Authentication routes (register, login, profile)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime

from models.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from auth.jwt_handler import create_access_token, get_current_user
from auth.password import hash_password, verify_password
from database.connection import get_database

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserRegister):
    """
    Register a new teacher account.
    
    - Checks for duplicate email
    - Hashes password with bcrypt
    - Returns JWT token immediately (auto-login after register)
    """
    db = get_database()

    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user document
    user_doc = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "school": user_data.school,
        "subject": user_data.subject,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate JWT token
    token = create_access_token({"sub": user_id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "school": user_data.school,
            "subject": user_data.subject,
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login with email and password.
    
    Returns JWT token on success.
    """
    db = get_database()

    # Find user by email
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "school": user.get("school"),
            "subject": user.get("subject"),
        },
    }


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current user's profile. Requires authentication."""
    return current_user


@router.put("/me")
async def update_profile(
    update_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update teacher profile (name, school, subject)."""
    db = get_database()
    from bson import ObjectId

    # Only allow safe fields to be updated
    allowed_fields = {"name", "school", "subject"}
    updates = {k: v for k, v in update_data.items() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": updates},
    )

    return {"message": "Profile updated successfully", **updates}
