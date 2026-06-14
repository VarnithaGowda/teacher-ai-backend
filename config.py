"""
config.py - Application configuration using Pydantic Settings
Reads from .env file automatically.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Teacher AI Platform"
    DEBUG: bool = True
    FRONTEND_URL: str = "https://teacher-ai-assist.netlify.app"

    # JWT
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "teacher_ai_db"

    # Gemini
    GEMINI_API_KEY: str = "AIzaSyDBER4HqkFKCrEYNn-MoJvff18klvCTyvc"
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cache settings so .env is only read once."""
    return Settings()


# Global settings instance
settings = get_settings()
