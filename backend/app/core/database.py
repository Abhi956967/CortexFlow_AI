import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger("cortexflow")

class InMemoryStore:
    """In-memory data store for local development when external DBs are not running."""
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.reset_tokens: Dict[str, Dict[str, Any]] = {}
        self.verification_tokens: Dict[str, Dict[str, Any]] = {}

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for u in self.users.values():
            if u.get("email", "").lower() == email.lower():
                return u
        return None

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(str(user_id))

    def insert_user(self, user_doc: Dict[str, Any]) -> str:
        user_id = str(uuid.uuid4())
        user_doc["_id"] = user_id
        user_doc["id"] = user_id
        user_doc["created_at"] = user_doc.get("created_at", datetime.utcnow())
        user_doc["is_verified"] = user_doc.get("is_verified", False)
        self.users[user_id] = user_doc
        return user_id

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = self.users.get(str(user_id))
        if user:
            user.update(updates)
            user["updated_at"] = datetime.utcnow()
            return user
        return None

    def delete_user(self, user_id: str):
        self.users.pop(str(user_id), None)
        # Delete user convs and messages
        user_conv_ids = [c["id"] for c in self.conversations.values() if str(c.get("userId")) == str(user_id)]
        for cid in user_conv_ids:
            self.conversations.pop(cid, None)
        self.messages = [m for m in self.messages if m.get("conversationId") not in user_conv_ids]

    # Reset Tokens
    def save_reset_token(self, user_id: str, token: str, expires_in_minutes: int = 15):
        self.reset_tokens[token] = {
            "user_id": str(user_id),
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            "used": False
        }

    def verify_reset_token(self, token: str) -> Optional[str]:
        entry = self.reset_tokens.get(token)
        if not entry:
            return None
        if entry["used"] or datetime.utcnow() > entry["expires_at"]:
            return None
        return entry["user_id"]

    def consume_reset_token(self, token: str):
        if token in self.reset_tokens:
            self.reset_tokens[token]["used"] = True

    # Email Verification
    def save_verification_token(self, user_id: str, token: str):
        self.verification_tokens[token] = {
            "user_id": str(user_id),
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "used": False
        }

    def verify_email_token(self, token: str) -> Optional[str]:
        entry = self.verification_tokens.get(token)
        if not entry or entry["used"] or datetime.utcnow() > entry["expires_at"]:
            return None
        entry["used"] = True
        user = self.users.get(entry["user_id"])
        if user:
            user["is_verified"] = True
        return entry["user_id"]

    # Sessions
    def save_session(self, user_id: str, refresh_token: str, expires_in_days: int = 30):
        session_id = str(uuid.uuid4())
        self.sessions[refresh_token] = {
            "id": session_id,
            "user_id": str(user_id),
            "refresh_token": refresh_token,
            "expires_at": datetime.utcnow() + timedelta(days=expires_in_days),
            "created_at": datetime.utcnow()
        }
        return session_id

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.sessions.values() if str(s.get("user_id")) == str(user_id)]

    def find_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        sess = self.sessions.get(refresh_token)
        if not sess or datetime.utcnow() > sess["expires_at"]:
            return None
        return sess

    def delete_session(self, refresh_token: str):
        self.sessions.pop(refresh_token, None)

    # Conversations & Messages
    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        convs = [c for c in self.conversations.values() if str(c.get("userId")) == str(user_id)]
        # Sort pinned first, then by updatedAt desc
        return sorted(convs, key=lambda x: (not x.get("isPinned", False), -x.get("updatedAt", datetime.utcnow()).timestamp() if isinstance(x.get("updatedAt"), datetime) else 0))

    def insert_conversation(self, conv_doc: Dict[str, Any]) -> str:
        conv_id = str(uuid.uuid4())
        conv_doc["_id"] = conv_id
        conv_doc["id"] = conv_id
        conv_doc["isPinned"] = conv_doc.get("isPinned", False)
        conv_doc["isArchived"] = conv_doc.get("isArchived", False)
        self.conversations[conv_id] = conv_doc
        return conv_id

    def update_conversation(self, conv_id: str, updates: Dict[str, Any]):
        if conv_id in self.conversations:
            self.conversations[conv_id].update(updates)
            self.conversations[conv_id]["updatedAt"] = datetime.utcnow()

    def delete_conversation(self, conv_id: str):
        self.conversations.pop(conv_id, None)
        self.messages = [m for m in self.messages if str(m.get("conversationId")) != str(conv_id)]

    def list_messages(self, conv_id: str) -> List[Dict[str, Any]]:
        msgs = [m for m in self.messages if str(m.get("conversationId")) == str(conv_id)]
        return sorted(msgs, key=lambda x: x.get("createdAt", datetime.utcnow()))

    def insert_message(self, msg_doc: Dict[str, Any]) -> str:
        msg_id = str(uuid.uuid4())
        msg_doc["_id"] = msg_id
        msg_doc["id"] = msg_id
        self.messages.append(msg_doc)
        if msg_doc.get("conversationId") in self.conversations:
            self.conversations[msg_doc["conversationId"]]["updatedAt"] = datetime.utcnow()
        return msg_id

    def update_message_feedback(self, message_id: str, rating: str):
        for m in self.messages:
            if str(m.get("id") or m.get("_id")) == str(message_id):
                m["feedback"] = rating
                break

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected: bool = False
        self.memory_store = InMemoryStore()

db_manager = DatabaseManager()

async def connect_to_mongo():
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000
        )
        await client.admin.command('ping')
        
        db_manager.client = client
        db_manager.db = client[settings.DATABASE_NAME]
        db_manager.is_connected = True
        
        await db_manager.db.users.create_index("email", unique=True)
        await db_manager.db.conversations.create_index([("userId", 1), ("isPinned", -1), ("updatedAt", -1)])
        await db_manager.db.messages.create_index([("conversationId", 1), ("createdAt", 1)])
        await db_manager.db.sessions.create_index("refresh_token")
        await db_manager.db.reset_tokens.create_index("token")
        await db_manager.db.verification_tokens.create_index("token")
        logger.info("✅ Connected to MongoDB Atlas / Cloud successfully.")
    except Exception as e:
        db_manager.client = None
        db_manager.db = None
        db_manager.is_connected = False
        logger.warning(f"⚠️ MongoDB not available ({e}). In-Memory Mock Store will be used for development.")

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        logger.info("Closed MongoDB connection.")

def get_db_manager() -> DatabaseManager:
    return db_manager

def get_database():
    return db_manager.db if db_manager.is_connected else None
