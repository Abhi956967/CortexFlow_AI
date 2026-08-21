import time
import urllib.parse
import httpx
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content
from app.core.storage import upload_file_artifact

logger = logging.getLogger("cortexflow")

IMAGE_PROMPT_SYSTEM = """You are an elite AI image prompt engineer.
Convert the user request into a highly detailed, cinematic, photorealistic image prompt.
Requirements:
- Cinematic 8k lighting, stunning details, professional camera composition, vivid colors.
- Return ONLY the enhanced English prompt without quotes or extra explanation.
"""

async def image_node(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "")
    llm = get_model("image")

    try:
        res = await llm.ainvoke([
            {"role": "system", "content": IMAGE_PROMPT_SYSTEM},
            {"role": "user", "content": prompt}
        ])
        enhanced_prompt = extract_text_content(res.content).strip()

        # Generate image using Pollinations AI free high-res rendering API
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(image_url)
            if resp.status_code == 200:
                filename = f"image_{int(time.time())}.png"
                download_url = await upload_file_artifact(resp.content, filename, "image/png")
                
                return {
                    **state,
                    "response": f"### 🎨 AI Image Generated\n\n**Prompt:** *{enhanced_prompt}*\n\n![Generated Image]({download_url})\n\n📥 **[Download High-Res Image]({download_url})**",
                    "images": [download_url],
                    "agent": "image"
                }

        return {
            **state,
            "response": f"### 🎨 AI Image Generated\n\n![Generated Image]({image_url})\n\n📥 [Direct Link]({image_url})",
            "images": [image_url],
            "agent": "image"
        }
    except Exception as e:
        logger.error(f"Image agent error: {e}")
        return {
            **state,
            "response": f"Failed to generate image: {str(e)}",
            "agent": "image"
        }
