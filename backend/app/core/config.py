import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "CortexFlow AI"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "cortexflow_super_secret_jwt_key_2026_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30         # 30 days

    # PostgreSQL / SQL Storage (Optional)
    DATABASE_URL: Optional[str] = None  # e.g. postgresql+asyncpg://user:pass@localhost:5432/cortexflow

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "cortexflow_ai"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    # AI API Keys
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Storage (Local or S3)
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    UPLOAD_DIR: str = "storage_uploads"
    STATIC_URL: str = "http://localhost:8000/storage"
    
    # Cookies & Security
    COOKIE_SECURE: bool = False  # Set to True in HTTPS production
    COOKIE_SAMESITE: str = "lax"
    FRONTEND_URL: str = "http://localhost:5173"

    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None

    # Razorpay (Optional for billing)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
