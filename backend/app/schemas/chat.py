from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class MessageCreate(BaseModel):
    conversationId: str
    role: str
    content: str
    images: Optional[List[str]] = []
    artifacts: Optional[List[Dict[str, Any]]] = []

class MessageResponse(BaseModel):
    id: str
    conversationId: str
    role: str
    content: str
    images: Optional[List[str]] = []
    artifacts: Optional[List[Dict[str, Any]]] = []
    createdAt: datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ConversationResponse(BaseModel):
    id: str
    userId: str
    title: str
    createdAt: datetime
    updatedAt: datetime
