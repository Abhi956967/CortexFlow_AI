from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AgentChatRequest(BaseModel):
    prompt: str
    conversationId: Optional[str] = None
    agent: Optional[str] = "router"  # "router", "chat", "coding", "search", "pdf", "ppt", "image", "vision", "pdf_rag"

class AgentChatResponse(BaseModel):
    success: bool
    answer: str
    agentUsed: Optional[str] = "chat"
    images: Optional[List[str]] = []
    artifacts: Optional[List[Dict[str, Any]]] = []
    creditsLeft: Optional[int] = 100
