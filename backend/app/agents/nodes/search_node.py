import logging
from app.agents.state import AgentState
from app.agents.tools.web_search import perform_web_search

logger = logging.getLogger("cortexflow")

async def search_node(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "")
    logger.info(f"Executing web search for query: {prompt}")

    try:
        search_results = await perform_web_search(prompt, max_results=5)
        return {
            **state,
            "searchResults": search_results,
            "agent": "search"
        }
    except Exception as e:
        logger.error(f"Search agent error: {e}")
        return {
            **state,
            "searchResults": "No search results found.",
            "agent": "search"
        }
