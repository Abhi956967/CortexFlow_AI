import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from app.core.config import settings

logger = logging.getLogger("cortexflow")

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    avatar = Column(Text, nullable=True)
    plan = Column(String(32), default="free")
    credits = Column(Integer, default=100)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="verification_tokens")

class PostgresManager:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.is_connected = False

postgres_manager = PostgresManager()

async def init_postgres():
    if not settings.DATABASE_URL:
        logger.info("ℹ️ No DATABASE_URL specified. Skipping PostgreSQL init.")
        return

    try:
        url = settings.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        postgres_manager.engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        postgres_manager.session_factory = async_sessionmaker(
            bind=postgres_manager.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with postgres_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        postgres_manager.is_connected = True
        logger.info("✅ Connected to PostgreSQL and initialized tables successfully.")
    except Exception as e:
        postgres_manager.is_connected = False
        logger.warning(f"⚠️ PostgreSQL not connected ({e}). Fallback stores will be used.")

async def close_postgres():
    if postgres_manager.engine:
        await postgres_manager.engine.dispose()
        logger.info("Closed PostgreSQL connection.")

async def get_postgres_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    if not postgres_manager.is_connected or not postgres_manager.session_factory:
        yield None
        return
    async with postgres_manager.session_factory() as session:
        yield session
