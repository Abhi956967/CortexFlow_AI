import json
import asyncio
import logging
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse
from app.core.security import get_optional_user
from app.core.redis_client import add_chat_memory, get_chat_memory
from app.agents.supervisor import multi_agent_graph
from app.schemas.agent import AgentChatResponse
from app.core.database import get_db_manager
from datetime import datetime

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
    Standard Multi-Agent AI execution endpoint.
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

    history = []
    if conversationId:
        history = await get_chat_memory(conversationId)

    initial_state = {
        "prompt": prompt,
        "conversationId": conversationId,
        "userId": user_id,
        "agent": agent if agent not in ["router", "auto", ""] else None,
        "file": file_info,
        "history": history
    }

    try:
        result_state = await multi_agent_graph.ainvoke(initial_state)
        
        response_text = result_state.get("response", "No response generated.")
        images = result_state.get("images", [])
        artifacts = result_state.get("artifacts", [])
        agent_used = result_state.get("agent", "chat")

        if conversationId:
            await add_chat_memory(conversationId, "user", prompt)
            await add_chat_memory(conversationId, "assistant", response_text)

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

@router.post("/stream")
async def execute_agent_stream(
    request: Request,
    prompt: str = Form(...),
    conversationId: Optional[str] = Form(None),
    agent: Optional[str] = Form("router"),
    file: Optional[UploadFile] = File(None),
    user: Optional[dict] = Depends(get_optional_user)
):
    """
    Streaming Multi-Agent AI execution endpoint (Server-Sent Events).
    Emits chunk events and final result payload.
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

    history = []
    if conversationId:
        history = await get_chat_memory(conversationId)

    initial_state = {
        "prompt": prompt,
        "conversationId": conversationId,
        "userId": user_id,
        "agent": agent if agent not in ["router", "auto", ""] else None,
        "file": file_info,
        "history": history
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Yield thinking status
            yield f"data: {json.dumps({'type': 'status', 'status': 'thinking', 'agent': agent})}\n\n"
            
            result_state = await multi_agent_graph.ainvoke(initial_state)
            response_text = result_state.get("response", "No response generated.")
            images = result_state.get("images", [])
            artifacts = result_state.get("artifacts", [])
            agent_used = result_state.get("agent", "chat")

            # Stream words with micro-delays for smooth streaming UX
            words = response_text.split(" ")
            accumulated = ""
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                accumulated += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk, 'full': accumulated})}\n\n"
                await asyncio.sleep(0.015)

            # Save to history & DB
            if conversationId:
                await add_chat_memory(conversationId, "user", prompt)
                await add_chat_memory(conversationId, "assistant", response_text)

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

            # Final done event
            yield f"data: {json.dumps({'type': 'done', 'answer': response_text, 'agentUsed': agent_used, 'images': images, 'artifacts': artifacts})}\n\n"

        except Exception as e:
            logger.error(f"Streaming agent error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
