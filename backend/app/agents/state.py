from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    prompt: str
    conversationId: Optional[str]
    userId: Optional[str]
    agent: Optional[str]
    file: Optional[Dict[str, Any]]        # Uploaded file info (bytes, name, path, content_type)
    history: Optional[List[Dict[str, str]]]
    searchResults: Optional[Any]
    response: Optional[str]
    images: Optional[List[str]]
    artifacts: Optional[List[Dict[str, Any]]]
    docs: Optional[List[Any]]
    next: Optional[str]
