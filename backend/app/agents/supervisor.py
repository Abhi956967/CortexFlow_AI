import logging
from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.nodes.router_node import router_node
from app.agents.nodes.chat_node import chat_node
from app.agents.nodes.coding_node import coding_node
from app.agents.nodes.search_node import search_node
from app.agents.nodes.pdf_gen_node import pdf_gen_node
from app.agents.nodes.ppt_node import ppt_node
from app.agents.nodes.image_node import image_node
from app.agents.nodes.vision_node import vision_node
from app.agents.nodes.rag_node import rag_node

logger = logging.getLogger("cortexflow")

# 1. Initialize StateGraph
builder = StateGraph(AgentState)

# 2. Add Nodes
builder.add_node("router", router_node)
builder.add_node("chat", chat_node)
builder.add_node("coding", coding_node)
builder.add_node("search", search_node)
builder.add_node("pdf", pdf_gen_node)
builder.add_node("ppt", ppt_node)
builder.add_node("image", image_node)
builder.add_node("vision", vision_node)
builder.add_node("pdf_rag", rag_node)

# 3. Add Edges
builder.add_edge(START, "router")

def route_next(state: AgentState) -> str:
    next_node = state.get("next", "chat")
    logger.info(f"Router decided target node: {next_node}")
    return next_node

builder.add_conditional_edges(
    "router",
    route_next,
    {
        "chat": "chat",
        "coding": "coding",
        "search": "search",
        "pdf": "pdf",
        "ppt": "ppt",
        "image": "image",
        "vision": "vision",
        "pdf_rag": "pdf_rag"
    }
)

# Search node feeds into chat for context synthesis
builder.add_edge("search", "chat")

# Terminal edges
builder.add_edge("chat", END)
builder.add_edge("coding", END)
builder.add_edge("pdf", END)
builder.add_edge("ppt", END)
builder.add_edge("image", END)
builder.add_edge("vision", END)
builder.add_edge("pdf_rag", END)

# Compile LangGraph
multi_agent_graph = builder.compile()
