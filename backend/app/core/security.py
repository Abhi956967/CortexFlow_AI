import secrets
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from bson import ObjectId
import bcrypt

security_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def set_auth_cookies(response: Response, access_token: str, refresh_token: Optional[str] = None):
    """
    Attaches secure HttpOnly cookies to response for seamless browser auth.
    """
    # 1. Access Token Cookie (1 day)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        expires=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/"
    )
    # 2. Refresh Token Cookie (30 days)
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=86400 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
            expires=86400 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
            samesite=settings.COOKIE_SAMESITE,
            secure=settings.COOKIE_SECURE,
            path="/"
        )

def clear_auth_cookies(response: Response):
    """
    Clears all auth cookies upon logout.
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

async def get_token_from_request(
    request: Request,
    token_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[str]:
    """
    Extracts token from either Authorization Bearer header OR HttpOnly access_token cookie.
    """
    if token_creds and token_creds.credentials:
        return token_creds.credentials
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    return None

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request)
) -> Dict[str, Any]:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id is None or token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")
    
    from app.core.database import get_db_manager
    mgr = get_db_manager()

    # 1. Check MongoDB
    if mgr.is_connected and mgr.db is not None:
        try:
            user = await mgr.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                return user
        except Exception:
            # Maybe string id
            user = await mgr.db.users.find_one({"_id": user_id})
            if user:
                user["id"] = str(user["_id"])
                return user

    # 2. Check In-Memory Store
    user = mgr.memory_store.find_user_by_id(user_id)
    if user:
        return user
        
    # Default fallback user if token was valid
    return {
        "id": user_id,
        "email": payload.get("email", "user@cortexflow.ai"),
        "name": payload.get("name", "Cortex User"),
        "credits": 100,
        "plan": "free"
    }

async def get_optional_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request)
) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        return await get_current_user(request, token)
    except HTTPException:
        return None
