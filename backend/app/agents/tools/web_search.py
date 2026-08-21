import os
import logging
from app.core.config import settings

logger = logging.getLogger("cortexflow")

async def perform_web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily if API key is present, else DuckDuckGo search.
    """
    tavily_key = settings.TAVILY_API_KEY or os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": max_results,
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    formatted = []
                    for r in results:
                        formatted.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nSnippet: {r.get('content')}")
                    return "\n\n".join(formatted)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")

    # Fallback to DuckDuckGo search
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            formatted = []
            for r in results:
                formatted.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}")
            return "\n\n".join(formatted)
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return f"Could not perform live web search for '{query}'. Please answer using general knowledge."
