import re
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("cortexflow")

ROUTER_PROMPT = """You are CortexFlow AI Supervisor and Router.
Classify the user request into ONE agent: coding, search, pdf, ppt, image, vision, pdf_rag, chat.
Output strictly ONLY the agent name without markdown or explanation."""

def fast_heuristic_router(prompt: str) -> str:
    """
    Ultra-fast 0ms rule-based intent router to avoid unnecessary LLM latency.
    """
    p = prompt.lower().strip()

    # 1. PPT / Presentation
    if any(k in p for k in ["ppt", "presentation", "powerpoint", "slides", "slide deck"]):
        return "ppt"

    # 2. PDF Document
    if any(k in p for k in ["pdf", "generate doc", "generate document", "create report pdf"]):
        return "pdf"

    # 3. AI Image Generation
    if any(k in p for k in ["generate image", "create image", "draw an image", "render image", "picture of", "photo of", "draw a"]):
        return "image"

    # 4. Web Search / Real-time info
    if any(k in p for k in ["weather in", "latest news", "today news", "live score", "current price of", "stock price of", "who won today"]):
        return "search"

    # 5. Coding & Development
    if any(k in p for k in [
        "write code", "create website", "build app", "create script", "python script", 
        "html", "css", "javascript", "react", "fastapi", "bug", "debug", "refactor",
        "sql query", "function to", "algorithm", "fix this error", "def ", "function()", "console.log"
    ]):
        return "coding"

    # 6. Default to Chat for general conversational queries
    return "chat"

async def router_node(state: AgentState) -> AgentState:
    # 1. If agent was explicitly selected in UI (Tabs: Chat, Coding, PDF, PPT, Image, Search)
    explicit_agent = state.get("agent")
    if explicit_agent and explicit_agent not in ["router", "auto", ""]:
        return {**state, "next": explicit_agent}

    # 2. Check for uploaded files
    uploaded_file = state.get("file")
    if uploaded_file:
        content_type = uploaded_file.get("content_type", "")
        filename = uploaded_file.get("filename", "").lower()
        if "pdf" in content_type or filename.endswith(".pdf"):
            return {**state, "next": "pdf_rag"}
        if "image" in content_type or any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            return {**state, "next": "vision"}

    # 3. 0ms Fast Heuristic Router (Instant, no LLM latency)
    prompt = state.get("prompt", "")
    fast_decision = fast_heuristic_router(prompt)
    if fast_decision:
        return {**state, "next": fast_decision}

    # 4. Fallback to LLM Router only if heuristic was inconclusive
    try:
        llm = get_model("chat")
        res = await llm.ainvoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=f"User Request: {prompt}")
        ])
        decision = extract_text_content(res.content).strip().lower()
        
        valid_agents = ["coding", "search", "pdf", "ppt", "image", "vision", "pdf_rag", "chat"]
        for agent in valid_agents:
            if agent in decision:
                return {**state, "next": agent}
        
        return {**state, "next": "chat"}
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {**state, "next": "chat"}
