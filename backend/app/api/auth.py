from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from datetime import datetime
from app.core.database import get_db_manager
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from app.schemas.auth import UserRegister, UserLogin, FirebaseLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister):
    mgr = get_db_manager()

    if mgr.is_connected:
        db = mgr.db
        existing = await db.users.find_one({"email": payload.email.lower()})
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user_doc = {
            "name": payload.name,
            "email": payload.email.lower(),
            "password": get_password_hash(payload.password),
            "credits": 100,
            "plan": "free",
            "createdAt": datetime.utcnow()
        }
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
    else:
        # In-Memory fallback
        existing = mgr.memory_store.find_user_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user_doc = {
            "name": payload.name,
            "email": payload.email.lower(),
            "password": get_password_hash(payload.password),
            "credits": 100,
            "plan": "free",
            "createdAt": datetime.utcnow()
        }
        user_id = mgr.memory_store.insert_user(user_doc)

    token = create_access_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": payload.name,
            "email": payload.email,
            "credits": 100,
            "plan": "free"
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    mgr = get_db_manager()

    if mgr.is_connected:
        db = mgr.db
        user = await db.users.find_one({"email": payload.email.lower()})
        if not user or not verify_password(payload.password, user.get("password", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user_id = str(user["_id"])
    else:
        # In-Memory fallback
        user = mgr.memory_store.find_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.get("password", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user_id = str(user["id"])

    token = create_access_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user.get("name", "User"),
            "email": user["email"],
            "avatar": user.get("avatar"),
            "credits": user.get("credits", 100),
            "plan": user.get("plan", "free")
        }
    }

@router.post("/firebase", response_model=TokenResponse)
async def firebase_auth(payload: FirebaseLogin):
    user_id = "firebase_user_123"
    token = create_access_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": "Google User",
            "email": "user@gmail.com",
            "credits": 100,
            "plan": "free"
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": str(user.get("id") or user.get("_id")),
        "name": user.get("name", "User"),
        "email": user.get("email", ""),
        "avatar": user.get("avatar"),
        "credits": user.get("credits", 100),
        "plan": user.get("plan", "free")
    }
