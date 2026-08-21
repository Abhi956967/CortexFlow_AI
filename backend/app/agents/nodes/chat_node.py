import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger("cortexflow")

CHAT_SYSTEM_PROMPT = """You are CortexFlow AI, a state-of-the-art intelligent multi-agent AI assistant.
You provide insightful, accurate, well-structured, and helpful answers.
- Format responses cleanly using Markdown (bolding, headers, code blocks, lists).
- If the previous agent provided search results, synthesize and cite them clearly.
- Maintain a friendly, professional, and knowledgeable persona.
"""

async def chat_node(state: AgentState) -> AgentState:
    llm = get_model("chat")
    prompt = state.get("prompt", "")
    history = state.get("history", [])
    search_results = state.get("searchResults")

    messages = [SystemMessage(content=CHAT_SYSTEM_PROMPT)]
    
    # Add conversation history
    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Add web search context if available
    user_content = prompt
    if search_results:
        user_content = f"Web Search Context:\n{search_results}\n\nUser Question:\n{prompt}"

    messages.append(HumanMessage(content=user_content))

    try:
        response = await llm.ainvoke(messages)
        return {
            **state,
            "response": extract_text_content(response.content),
            "agent": "chat"
        }
    except Exception as e:
        logger.error(f"Chat agent error: {e}")
        return {
            **state,
            "response": f"I encountered an error processing your message: {str(e)}",
            "agent": "chat"
        }
