from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import PlainTextResponse
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

class PinConvPayload(BaseModel):
    conversationId: str
    isPinned: bool

class ArchiveConvPayload(BaseModel):
    conversationId: str
    isArchived: bool

class FeedbackPayload(BaseModel):
    messageId: str
    rating: str  # "like" | "dislike"

class EditMessagePayload(BaseModel):
    messageId: str
    content: str

@router.get("/get-conversations")
@router.get("/conversations")
async def list_conversations(user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    user_id = str(user.get("id") or user.get("_id")) if user else "anonymous"

    if mgr.is_connected and mgr.db is not None:
        cursor = mgr.db.conversations.find({"userId": user_id}).sort([("isPinned", -1), ("updatedAt", -1)])
        convs = await cursor.to_list(length=100)
    else:
        convs = mgr.memory_store.list_conversations(user_id)
    
    return [
        {
            "_id": str(c.get("_id") or c.get("id")),
            "id": str(c.get("_id") or c.get("id")),
            "userId": c.get("userId", user_id),
            "title": c.get("title", "New Chat"),
            "isPinned": c.get("isPinned", False),
            "isArchived": c.get("isArchived", False),
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
        "isPinned": False,
        "isArchived": False,
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
        "isPinned": False,
        "isArchived": False,
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
        mgr.memory_store.update_conversation(payload.conversationId, {"title": payload.title})
    return {"success": True, "title": payload.title}

@router.post("/pin-conversation")
async def pin_conversation(payload: PinConvPayload, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.conversations.update_one(
                {"_id": ObjectId(payload.conversationId)},
                {"$set": {"isPinned": payload.isPinned, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            pass
    else:
        mgr.memory_store.update_conversation(payload.conversationId, {"isPinned": payload.isPinned})
    return {"success": True, "isPinned": payload.isPinned}

@router.post("/archive-conversation")
async def archive_conversation(payload: ArchiveConvPayload, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.conversations.update_one(
                {"_id": ObjectId(payload.conversationId)},
                {"$set": {"isArchived": payload.isArchived, "updatedAt": datetime.utcnow()}}
            )
        except Exception:
            pass
    else:
        mgr.memory_store.update_conversation(payload.conversationId, {"isArchived": payload.isArchived})
    return {"success": True, "isArchived": payload.isArchived}

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
            "feedback": m.get("feedback"),
            "createdAt": m.get("createdAt", datetime.utcnow()).isoformat() if isinstance(m.get("createdAt"), datetime) else str(m.get("createdAt"))
        }
        for m in msgs
    ]

@router.post("/feedback")
async def submit_feedback(payload: FeedbackPayload, user: Optional[dict] = Depends(get_optional_user)):
    mgr = get_db_manager()
    if mgr.is_connected and mgr.db is not None:
        try:
            await mgr.db.messages.update_one(
                {"_id": ObjectId(payload.messageId)},
                {"$set": {"feedback": payload.rating}}
            )
        except Exception:
            pass
    else:
        mgr.memory_store.update_message_feedback(payload.messageId, payload.rating)
    return {"success": True, "rating": payload.rating}

@router.get("/export/{conversation_id}")
async def export_conversation(conversation_id: str, format: str = Query("markdown")):
    mgr = get_db_manager()
    conv = None
    msgs = []

    if mgr.is_connected and mgr.db is not None:
        try:
            conv = await mgr.db.conversations.find_one({"_id": ObjectId(conversation_id)})
            cursor = mgr.db.messages.find({"conversationId": conversation_id}).sort("createdAt", 1)
            msgs = await cursor.to_list(length=200)
        except Exception:
            pass
    else:
        conv = mgr.memory_store.conversations.get(conversation_id)
        msgs = mgr.memory_store.list_messages(conversation_id)

    title = conv.get("title", "CortexAI Conversation") if conv else "CortexAI Conversation"

    if format == "markdown":
        md = f"# {title}\n\n*Exported from CortexFlow AI on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n---\n\n"
        for m in msgs:
            role = "👤 User" if m["role"] == "user" else "🤖 CortexAI"
            md += f"### {role}\n\n{m['content']}\n\n"
            if m.get("images"):
                for img in m["images"]:
                    md += f"![Image]({img})\n\n"
            md += "---\n\n"
        return PlainTextResponse(content=md, media_type="text/markdown")

    text = f"{title}\n\n"
    for m in msgs:
        role = "User" if m["role"] == "user" else "CortexAI"
        text += f"[{role}]:\n{m['content']}\n\n"
    return PlainTextResponse(content=text, media_type="text/plain")

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
