import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.redis_client import connect_to_redis, close_redis_connection
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.api.billing import router as billing_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting CortexFlow AI Backend (FastAPI + LangGraph)...")
    await connect_to_mongo()
    await connect_to_redis()
    yield
    # Shutdown
    print("🛑 Shutting down CortexFlow AI Backend...")
    await close_mongo_connection()
    await close_redis_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Ready Python Multi-Agent AI Platform Backend using FastAPI, LangGraph, Qdrant, and MongoDB",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Storage directory for generated artifacts (PDF, PPT, Images)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.UPLOAD_DIR), name="storage")

# Include API Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)
app.include_router(billing_router, prefix=settings.API_V1_STR)

@app.get("/api/me")
async def get_current_user_profile():
    return {
        "user": {
            "id": "cortex_user_1",
            "name": "Cortex User",
            "email": "user@cortexflow.ai",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Cortex",
            "credits": 100,
            "plan": "free"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "engine": "Python LangGraph + FastAPI"
    }

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Backend API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
