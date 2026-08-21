import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger("cortexflow")

class InMemoryStore:
    """In-memory data store for local development when MongoDB is not running."""
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []

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
        self.users[user_id] = user_doc
        return user_id

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        convs = [c for c in self.conversations.values() if str(c.get("userId")) == str(user_id)]
        return sorted(convs, key=lambda x: x.get("updatedAt", datetime.utcnow()), reverse=True)

    def insert_conversation(self, conv_doc: Dict[str, Any]) -> str:
        conv_id = str(uuid.uuid4())
        conv_doc["_id"] = conv_id
        conv_doc["id"] = conv_id
        self.conversations[conv_id] = conv_doc
        return conv_id

    def update_conversation(self, conv_id: str, title: str):
        if conv_id in self.conversations:
            self.conversations[conv_id]["title"] = title
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

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected: bool = False
        self.memory_store = InMemoryStore()

db_manager = DatabaseManager()

async def connect_to_mongo():
    try:
        # Connect with short timeout so it doesn't hang if MongoDB isn't running locally
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000
        )
        # Ping server to verify connectivity
        await client.admin.command('ping')
        
        db_manager.client = client
        db_manager.db = client[settings.DATABASE_NAME]
        db_manager.is_connected = True
        
        # Create indexes
        await db_manager.db.users.create_index("email", unique=True)
        await db_manager.db.conversations.create_index([("userId", 1), ("updatedAt", -1)])
        await db_manager.db.messages.create_index([("conversationId", 1), ("createdAt", 1)])
        logger.info("✅ Connected to MongoDB successfully.")
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
