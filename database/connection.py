"""
database/connection.py - MongoDB async connection using Motor
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

# Global client and db references
client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    """Create MongoDB connection on app startup."""
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # Verify connection
        await client.admin.command("ping")
        logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection on app shutdown."""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")


def get_database():
    """Return the database instance (used as a dependency)."""
    return db
