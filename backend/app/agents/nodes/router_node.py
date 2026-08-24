import re
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("cortexflow")

ROUTER_PROMPT = """You are CortexFlow AI Supervisor and Intent Router.
Classify the user request into EXACTLY ONE of the following agents:
- search: if the user asks for real-time information, current events, weather, stock prices, sports scores, news, or latest facts.
- coding: if the user asks to write code, debug, create apps, scripts, or components.
- pdf: if the user asks to generate a downloadable PDF document or report.
- ppt: if the user asks to generate a PowerPoint slide deck or presentation.
- image: if the user asks to generate, draw, or render an image.
- data_analysis: if the user asks to analyze numbers, statistics, CSV, or dataset tables.
- agents_team: if the user asks for multi-agent swarm deliberation, architecture critique, or multi-perspective review.
- chat: for general reasoning, explanations, creative writing, or friendly conversation.

Output strictly ONLY the agent name without markdown, quotes, or punctuation."""

def fast_heuristic_router(prompt: str) -> str:
    p = prompt.lower().strip()

    # 1. PPT / Presentation
    if any(k in p for k in ["ppt", "presentation", "powerpoint", "slides", "slide deck"]):
        return "ppt"

    # 2. PDF Document Generation
    if any(k in p for k in ["generate doc", "generate document", "create report pdf", "build pdf", "create a pdf", "make a pdf"]):
        return "pdf"

    # 3. AI Image Generation
    if any(k in p for k in ["generate image", "create image", "draw an image", "render image", "picture of", "photo of", "draw a", "generate a pic"]):
        return "image"

    # 4. Web Search / Real-time info (Weather, News, Stocks, Sports, Facts)
    if any(k in p for k in [
        "weather", "wether", "temprature", "temperature", "forecast", "climate in",
        "latest news", "today news", "live score", "current price", "stock price",
        "who won", "who is the current", "who is the prime minister", "who is president",
        "what is happening in", "current status of", "breaking news", "recent news",
        "live updates", "live update", "search the web", "search online"
    ]):
        return "search"

    # 5. Data Analysis / CSV / Excel
    if any(k in p for k in ["analyze data", "csv", "excel", "dataset", "statistics", "trend analysis", "data insights", "analyze table"]):
        return "data_analysis"

    # 6. Multi-Agent Team Swarm
    if any(k in p for k in ["agent team", "multi-agent", "swarm", "deliberate", "architect review", "planner and critic"]):
        return "agents_team"

    # 7. Coding & Development
    if any(k in p for k in [
        "write code", "create website", "build app", "create script", "python script", 
        "html", "css", "javascript", "react", "fastapi", "bug", "debug", "refactor",
        "sql query", "function to", "algorithm", "fix this error", "def ", "function()", "console.log"
    ]):
        return "coding"

    return ""

async def router_node(state: AgentState) -> AgentState:
    explicit_agent = state.get("agent")
    if explicit_agent and explicit_agent not in ["router", "auto", ""]:
        # Map aliases
        if explicit_agent in ["data", "analysis"]:
            explicit_agent = "data_analysis"
        if explicit_agent in ["agents", "team"]:
            explicit_agent = "agents_team"
        if explicit_agent in ["rag", "knowledge"]:
            explicit_agent = "pdf_rag"
        return {**state, "next": explicit_agent}

    # Uploaded file routing
    uploaded_file = state.get("file")
    if uploaded_file:
        content_type = uploaded_file.get("content_type", "")
        filename = uploaded_file.get("filename", "").lower()
        if "pdf" in content_type or filename.endswith(".pdf"):
            return {**state, "next": "pdf_rag"}
        if any(filename.endswith(ext) for ext in [".csv", ".tsv", ".xlsx", ".xls", ".json"]):
            return {**state, "next": "data_analysis"}
        if "image" in content_type or any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            return {**state, "next": "vision"}

    # 0ms Heuristic fast route
    prompt = state.get("prompt", "")
    fast_decision = fast_heuristic_router(prompt)
    if fast_decision:
        return {**state, "next": fast_decision}

    # LLM Router fallback
    try:
        llm = get_model("chat")
        res = await llm.ainvoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=f"User Request: {prompt}")
        ])
        decision = extract_text_content(res.content).strip().lower()
        
        valid_agents = ["coding", "search", "pdf", "ppt", "image", "vision", "pdf_rag", "data_analysis", "agents_team", "chat"]
        for agent in valid_agents:
            if agent in decision:
                return {**state, "next": agent}
        
        return {**state, "next": "chat"}
    except Exception as e:
        logger.error(f"Router error: {e}")
        return {**state, "next": "chat"}
