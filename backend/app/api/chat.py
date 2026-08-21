from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db_manager
from app.core.security import get_optional_user
from app.schemas.chat import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

class UpdateConvPayload(BaseModel):
    conversationId: str
    title: str

@router.get("/get-conversations")
@router.get("/conversations")
async def list_conversations(user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    user_id = str(user.get("id") or user.get("_id")) if user else "anonymous"

    if mgr.is_connected and mgr.db is not None:
        cursor = mgr.db.conversations.find({"userId": user_id}).sort("updatedAt", -1)
        convs = await cursor.to_list(length=100)
    else:
        convs = mgr.memory_store.list_conversations(user_id)
    
    return [
        {
            "_id": str(c.get("_id") or c.get("id")),
            "id": str(c.get("_id") or c.get("id")),
            "userId": c.get("userId", user_id),
            "title": c.get("title", "New Chat"),
            "createdAt": c.get("createdAt", datetime.utcnow()).isoformat() if isinstance(c.get("createdAt"), datetime) else str(c.get("createdAt")),
            "updatedAt": c.get("updatedAt", datetime.utcnow()).isoformat() if isinstance(c.get("updatedAt"), datetime) else str(c.get("updatedAt"))
        }
        for c in convs
    ]

@router.post("/create-conversation")
@router.post("/conversations")
async def create_conversation(payload: Optional[ConversationCreate] = None, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    user_id = str(user.get("id") or user.get("_id")) if user else "anonymous"
    title = payload.title if payload and payload.title else "New Chat"
    doc = {
        "userId": user_id,
        "title": title,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    if mgr.is_connected and mgr.db is not None:
        res = await mgr.db.conversations.insert_one(doc)
        doc_id = str(res.inserted_id)
    else:
        doc_id = mgr.memory_store.insert_conversation(doc)

    return {
        "_id": doc_id,
        "id": doc_id,
        "userId": user_id,
        "title": title,
        "createdAt": doc["createdAt"].isoformat(),
        "updatedAt": doc["updatedAt"].isoformat()
    }

@router.post("/update-conversation")
async def update_conversation(payload: UpdateConvPayload, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.conversations.update_one(
                {"_id": ObjectId(payload.conversationId)},
                {"$set": {"title": payload.title, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            pass
    else:
        mgr.memory_store.update_conversation(payload.conversationId, payload.title)
    return {"success": True, "title": payload.title}

@router.get("/get-messages/{conversation_id}")
@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()

    if mgr.is_connected and mgr.db is not None:
        cursor = mgr.db.messages.find({"conversationId": conversation_id}).sort("createdAt", 1)
        msgs = await cursor.to_list(length=200)
    else:
        msgs = mgr.memory_store.list_messages(conversation_id)
    
    return [
        {
            "_id": str(m.get("_id") or m.get("id")),
            "id": str(m.get("_id") or m.get("id")),
            "conversationId": m["conversationId"],
            "role": m["role"],
            "content": m["content"],
            "images": m.get("images", []),
            "artifacts": m.get("artifacts", []),
            "createdAt": m.get("createdAt", datetime.utcnow()).isoformat() if isinstance(m.get("createdAt"), datetime) else str(m.get("createdAt"))
        }
        for m in msgs
    ]

@router.post("/save-message")
async def save_message(payload: MessageCreate):
    mgr = get_db_manager()
    doc = {
        "conversationId": payload.conversationId,
        "role": payload.role,
        "content": payload.content,
        "images": payload.images or [],
        "artifacts": payload.artifacts or [],
        "createdAt": datetime.utcnow()
    }
    
    if mgr.is_connected and mgr.db is not None:
        res = await mgr.db.messages.insert_one(doc)
        msg_id = str(res.inserted_id)
        try:
            await mgr.db.conversations.update_one(
                {"_id": ObjectId(payload.conversationId)},
                {"$set": {"updatedAt": datetime.utcnow()}}
            )
        except Exception:
            pass
    else:
        msg_id = mgr.memory_store.insert_message(doc)

    return {
        "_id": msg_id,
        "id": msg_id,
        "conversationId": payload.conversationId,
        "role": payload.role,
        "content": payload.content,
        "images": payload.images or [],
        "artifacts": payload.artifacts or [],
        "createdAt": doc["createdAt"].isoformat()
    }

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.conversations.delete_one({"_id": ObjectId(conversation_id)})
            await mgr.db.messages.delete_many({"conversationId": conversation_id})
        except Exception:
            pass
    else:
        mgr.memory_store.delete_conversation(conversation_id)
    return {"success": True, "message": "Conversation deleted"}
