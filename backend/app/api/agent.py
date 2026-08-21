import json
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse
from app.core.security import get_optional_user
from app.core.redis_client import add_chat_memory, get_chat_memory
from app.core.database import get_database
from app.agents.supervisor import multi_agent_graph
from app.schemas.agent import AgentChatResponse

router = APIRouter(prefix="/agent", tags=["Agent"])
logger = logging.getLogger("cortexflow")

@router.post("/chat", response_model=AgentChatResponse)
async def execute_agent(
    request: Request,
    prompt: str = Form(...),
    conversationId: Optional[str] = Form(None),
    agent: Optional[str] = Form("router"),
    file: Optional[UploadFile] = File(None),
    user: Optional[dict] = Depends(get_optional_user)
):
    """
    Main Multi-Agent AI execution endpoint.
    Invokes LangGraph StateGraph (Router -> Specialized Agent -> Response).
    """
    user_id = user.get("id") if user else "anonymous"
    file_info = None

    if file:
        file_bytes = await file.read()
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "bytes": file_bytes
        }

    # Fetch conversation memory from Redis
    history = []
    if conversationId:
        history = await get_chat_memory(conversationId)

    # Prepare initial state
    initial_state = {
        "prompt": prompt,
        "conversationId": conversationId,
        "userId": user_id,
        "agent": agent if agent != "router" else None,
        "file": file_info,
        "history": history
    }

    # Execute LangGraph Multi-Agent Engine
    try:
        result_state = await multi_agent_graph.ainvoke(initial_state)
        
        response_text = result_state.get("response", "No response generated.")
        images = result_state.get("images", [])
        artifacts = result_state.get("artifacts", [])
        agent_used = result_state.get("agent", "chat")

        # Save to Redis memory
        if conversationId:
            await add_chat_memory(conversationId, "user", prompt)
            await add_chat_memory(conversationId, "assistant", response_text)

        # Save to Database (MongoDB or MemoryStore fallback)
        if conversationId:
            from datetime import datetime
            from app.core.database import get_db_manager
            mgr = get_db_manager()
            user_msg = {
                "conversationId": conversationId,
                "role": "user",
                "content": prompt,
                "createdAt": datetime.utcnow()
            }
            assistant_msg = {
                "conversationId": conversationId,
                "role": "assistant",
                "content": response_text,
                "images": images,
                "artifacts": artifacts,
                "createdAt": datetime.utcnow()
            }
            if mgr.is_connected and mgr.db is not None:
                await mgr.db.messages.insert_one(user_msg)
                await mgr.db.messages.insert_one(assistant_msg)
            else:
                mgr.memory_store.insert_message(user_msg)
                mgr.memory_store.insert_message(assistant_msg)

        return {
            "success": True,
            "answer": response_text,
            "agentUsed": agent_used,
            "images": images,
            "artifacts": artifacts,
            "creditsLeft": 95
        }

    except Exception as e:
        logger.error(f"Error in multi-agent execution: {e}", exc_info=True)
        return {
            "success": False,
            "answer": f"Error executing agent workflow: {str(e)}",
            "agentUsed": "error",
            "images": [],
            "artifacts": [],
            "creditsLeft": 100
        }
