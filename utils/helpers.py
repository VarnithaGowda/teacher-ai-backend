"""
utils/helpers.py - General utility functions
"""

import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from config import settings
import logging

logger = logging.getLogger(__name__)


async def save_upload_file(upload_file: UploadFile, user_id: str) -> tuple[str, str]:
    """
    Save an uploaded file to disk.
    
    Args:
        upload_file: FastAPI UploadFile object
        user_id: User ID (for organizing uploads)
    
    Returns:
        Tuple of (file_path, original_filename)
    
    Raises:
        HTTPException if file is too large or type is invalid
    """
    # Check file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await upload_file.read()
    
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Create user-specific upload directory
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    # Generate unique filename to avoid collisions
    ext = upload_file.filename.rsplit(".", 1)[-1] if "." in upload_file.filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(user_dir, unique_filename)

    # Write file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(f"Saved upload: {file_path} ({len(content)} bytes)")
    return file_path, upload_file.filename


def format_mongo_doc(doc: dict) -> dict:
    """Convert MongoDB _id to string id."""
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc
