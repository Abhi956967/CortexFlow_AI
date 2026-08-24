import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from bson import ObjectId
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db_manager
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_random_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    FirebaseLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    UserResponse,
    TokenResponse,
    MessageResponse
)

logger = logging.getLogger("cortexflow")
router = APIRouter(prefix="/auth", tags=["Auth"])

# ─── 1. Register ─────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister, response: Response):
    mgr = get_db_manager()
    email_clean = payload.email.lower().strip()

    # Check MongoDB
    if mgr.is_connected and mgr.db is not None:
        db = mgr.db
        existing = await db.users.find_one({"email": email_clean})
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

        user_doc = {
            "name": payload.name.strip(),
            "email": email_clean,
            "password": get_password_hash(payload.password),
            "avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={payload.name.strip()}",
            "credits": 100,
            "plan": "free",
            "is_verified": False,
            "createdAt": datetime.utcnow()
        }
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        user_doc["id"] = user_id
    else:
        # Check In-Memory fallback
        existing = mgr.memory_store.find_user_by_email(email_clean)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

        user_doc = {
            "name": payload.name.strip(),
            "email": email_clean,
            "password": get_password_hash(payload.password),
            "avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={payload.name.strip()}",
            "credits": 100,
            "plan": "free",
            "is_verified": False,
            "createdAt": datetime.utcnow()
        }
        user_id = mgr.memory_store.insert_user(user_doc)

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Save session
    if mgr.is_connected and mgr.db is not None:
        await mgr.db.sessions.insert_one({
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        })
    else:
        mgr.memory_store.save_session(user_id, refresh_token)

    # Set secure HttpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "name": user_doc["name"],
            "email": user_doc["email"],
            "avatar": user_doc.get("avatar"),
            "credits": user_doc.get("credits", 100),
            "plan": user_doc.get("plan", "free"),
            "is_verified": user_doc.get("is_verified", False)
        }
    }

# ─── 2. Login ────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, response: Response):
    mgr = get_db_manager()
    email_clean = payload.email.lower().strip()

    user = None
    user_id = None

    if mgr.is_connected and mgr.db is not None:
        user = await mgr.db.users.find_one({"email": email_clean})
        if not user or not verify_password(payload.password, user.get("password", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user_id = str(user["_id"])
    else:
        user = mgr.memory_store.find_user_by_email(email_clean)
        if not user or not verify_password(payload.password, user.get("password", "")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user_id = str(user["id"])

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Save session
    if mgr.is_connected and mgr.db is not None:
        await mgr.db.sessions.insert_one({
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        })
    else:
        mgr.memory_store.save_session(user_id, refresh_token)

    # Set secure HttpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "name": user.get("name", "Cortex User"),
            "email": user.get("email", email_clean),
            "avatar": user.get("avatar") or f"https://api.dicebear.com/7.x/bottts/svg?seed={user.get('name', 'User')}",
            "credits": user.get("credits", 100),
            "plan": user.get("plan", "free"),
            "is_verified": user.get("is_verified", False)
        }
    }

# ─── 3. Logout ───────────────────────────────────────────────────────────────
@router.post("/logout", response_model=MessageResponse)
@router.get("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        mgr = get_db_manager()
        if mgr.is_connected and mgr.db is not None:
            try:
                await mgr.db.sessions.delete_many({"refresh_token": refresh_token})
            except Exception:
                pass
        else:
            mgr.memory_store.delete_session(refresh_token)

    clear_auth_cookies(response)
    return {"success": True, "message": "Successfully logged out"}

# ─── 4. Current User Profile (/auth/me) ──────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    user_id = str(user.get("id") or user.get("_id"))
    return {
        "id": user_id,
        "name": user.get("name", "Cortex User"),
        "email": user.get("email", ""),
        "avatar": user.get("avatar") or f"https://api.dicebear.com/7.x/bottts/svg?seed={user.get('name', 'User')}",
        "credits": user.get("credits", 100),
        "plan": user.get("plan", "free"),
        "is_verified": user.get("is_verified", False)
    }

# ─── 5. Refresh Token (/auth/refresh) ────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # Check authorization header fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if not user_id or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

    mgr = get_db_manager()
    user = None
    if mgr.is_connected and mgr.db is not None:
        try:
            user = await mgr.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            user = await mgr.db.users.find_one({"_id": user_id})
    else:
        user = mgr.memory_store.find_user_by_id(user_id)

    if not user:
        user = {"id": user_id, "name": "Cortex User", "email": "user@cortexflow.ai", "credits": 100, "plan": "free"}

    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    set_auth_cookies(response, new_access_token, new_refresh_token)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
        "user": {
            "id": user_id,
            "name": user.get("name", "Cortex User"),
            "email": user.get("email", ""),
            "avatar": user.get("avatar"),
            "credits": user.get("credits", 100),
            "plan": user.get("plan", "free"),
            "is_verified": user.get("is_verified", False)
        }
    }

# ─── 6. Forgot Password ──────────────────────────────────────────────────────
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest):
    mgr = get_db_manager()
    email_clean = payload.email.lower().strip()

    user = None
    if mgr.is_connected and mgr.db is not None:
        user = await mgr.db.users.find_one({"email": email_clean})
    else:
        user = mgr.memory_store.find_user_by_email(email_clean)

    if not user:
        # Do not leak user existence, return friendly success
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    user_id = str(user.get("_id") or user.get("id"))
    reset_token = generate_random_token(32)

    if mgr.is_connected and mgr.db is not None:
        await mgr.db.reset_tokens.insert_one({
            "user_id": user_id,
            "token": reset_token,
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "used": False,
            "created_at": datetime.utcnow()
        })
    else:
        mgr.memory_store.save_reset_token(user_id, reset_token)

    logger.info(f"🔑 Password reset token generated for {email_clean}: {reset_token}")

    return {
        "success": True,
        "message": "Password reset instructions have been generated. Use the token to reset your password.",
        "reset_token": reset_token
    }

# ─── 7. Reset Password ───────────────────────────────────────────────────────
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest):
    mgr = get_db_manager()
    user_id = None

    if mgr.is_connected and mgr.db is not None:
        token_doc = await mgr.db.reset_tokens.find_one({
            "token": payload.token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if not token_doc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        
        user_id = token_doc["user_id"]
        hashed_password = get_password_hash(payload.new_password)

        try:
            await mgr.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            await mgr.db.users.update_one(
                {"_id": user_id},
                {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
            )

        await mgr.db.reset_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
    else:
        user_id = mgr.memory_store.verify_reset_token(payload.token)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        
        hashed_password = get_password_hash(payload.new_password)
        mgr.memory_store.update_user(user_id, {"password": hashed_password})
        mgr.memory_store.consume_reset_token(payload.token)

    return {
        "success": True,
        "message": "Password has been successfully updated. You can now login with your new password."
    }

# ─── 8. Verify Email ─────────────────────────────────────────────────────────
@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        token_doc = await mgr.db.verification_tokens.find_one({
            "token": payload.token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if not token_doc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
        
        user_id = token_doc["user_id"]
        try:
            await mgr.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_verified": True}})
        except Exception:
            await mgr.db.users.update_one({"_id": user_id}, {"$set": {"is_verified": True}})
        await mgr.db.verification_tokens.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})
    else:
        user_id = mgr.memory_store.verify_email_token(payload.token)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    return {"success": True, "message": "Email successfully verified!"}

# ─── 9. Update Profile ───────────────────────────────────────────────────────
@router.put("/profile", response_model=UserResponse)
async def update_profile(payload: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    user_id = str(user.get("id") or user.get("_id"))
    mgr = get_db_manager()

    updates = {}
    if payload.name:
        updates["name"] = payload.name.strip()
    if payload.avatar:
        updates["avatar"] = payload.avatar

    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {**updates, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            await mgr.db.users.update_one(
                {"_id": user_id},
                {"$set": {**updates, "updatedAt": datetime.utcnow()}}
            )
    else:
        mgr.memory_store.update_user(user_id, updates)

    updated_name = updates.get("name", user.get("name", "Cortex User"))
    updated_avatar = updates.get("avatar", user.get("avatar"))

    return {
        "id": user_id,
        "name": updated_name,
        "email": user.get("email", ""),
        "avatar": updated_avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={updated_name}",
        "credits": user.get("credits", 100),
        "plan": user.get("plan", "free"),
        "is_verified": user.get("is_verified", False)
    }

# ─── 10. Change Password ─────────────────────────────────────────────────────
@router.post("/change-password", response_model=MessageResponse)
async def change_password(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    user_id = str(user.get("id") or user.get("_id"))
    mgr = get_db_manager()

    current_hashed = user.get("password", "")
    if not verify_password(payload.current_password, current_hashed):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

    new_hash = get_password_hash(payload.new_password)
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_hash, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            await mgr.db.users.update_one(
                {"_id": user_id},
                {"$set": {"password": new_hash, "updatedAt": datetime.utcnow()}}
            )
    else:
        mgr.memory_store.update_user(user_id, {"password": new_hash})

    return {"success": True, "message": "Password changed successfully"}

# ─── 11. OAuth / Firebase Unified Handler ────────────────────────────────────
@router.post("/firebase", response_model=TokenResponse)
@router.post("/oauth", response_model=TokenResponse)
async def oauth_login(payload: FirebaseLogin, response: Response):
    mgr = get_db_manager()
    email = (payload.email or "google.user@cortexflow.ai").lower().strip()
    name = payload.name or "Cortex User"
    avatar = payload.avatar or f"https://api.dicebear.com/7.x/bottts/svg?seed={name}"

    user = None
    user_id = None

    if mgr.is_connected and mgr.db is not None:
        user = await mgr.db.users.find_one({"email": email})
        if not user:
            user_doc = {
                "name": name,
                "email": email,
                "avatar": avatar,
                "credits": 100,
                "plan": "free",
                "is_verified": True,
                "createdAt": datetime.utcnow()
            }
            res = await mgr.db.users.insert_one(user_doc)
            user_id = str(res.inserted_id)
            user = user_doc
        else:
            user_id = str(user["_id"])
    else:
        user = mgr.memory_store.find_user_by_email(email)
        if not user:
            user_doc = {
                "name": name,
                "email": email,
                "avatar": avatar,
                "credits": 100,
                "plan": "free",
                "is_verified": True,
                "createdAt": datetime.utcnow()
            }
            user_id = mgr.memory_store.insert_user(user_doc)
            user = user_doc
        else:
            user_id = str(user["id"])

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "name": user.get("name", name),
            "email": email,
            "avatar": user.get("avatar", avatar),
            "credits": user.get("credits", 100),
            "plan": user.get("plan", "free"),
            "is_verified": user.get("is_verified", True)
        }
    }
