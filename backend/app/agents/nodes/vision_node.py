import base64
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from langchain_core.messages import HumanMessage

logger = logging.getLogger("cortexflow")

async def vision_node(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "Analyze and describe this image in detail.")
    file_info = state.get("file")
    llm = get_model("chat")

    if not file_info:
        return {
            **state,
            "response": "No image file provided for vision analysis.",
            "agent": "vision"
        }

    try:
        file_bytes = file_info.get("bytes")
        content_type = file_info.get("content_type", "image/jpeg")
        base64_image = base64.b64encode(file_bytes).decode("utf-8")

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{content_type};base64,{base64_image}"},
                },
            ]
        )

        response = await llm.ainvoke([message])
        return {
            **state,
            "response": extract_text_content(response.content),
            "agent": "vision"
        }
    except Exception as e:
        logger.error(f"Vision agent error: {e}")
        return {
            **state,
            "response": f"Failed to analyze image: {str(e)}",
            "agent": "vision"
        }
