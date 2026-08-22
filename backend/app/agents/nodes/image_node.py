import time
import urllib.parse
import logging
from app.agents.state import AgentState
from app.agents.llm import get_model, extract_text_content

logger = logging.getLogger("cortexflow")

IMAGE_PROMPT_SYSTEM = """You are an elite AI image prompt engineer.
Convert the user request into a highly detailed, cinematic, photorealistic or stylized image prompt matching the requested style (e.g. cartoon, anime, 3d render, photorealistic).
Requirements:
- Stunning details, artistic style, professional composition, vivid lighting.
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
        if not enhanced_prompt:
            enhanced_prompt = prompt

        seed = int(time.time() * 1000) % 1000000
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"

        return {
            **state,
            "response": f"### 🎨 AI Image Generated\n\n**Prompt:** *{enhanced_prompt}*\n\n![Generated Image]({image_url})\n\n📥 **[Open Full Resolution Image]({image_url})**",
            "images": [image_url],
            "agent": "image"
        }
    except Exception as e:
        logger.error(f"Image agent error: {e}")
        encoded_fallback = urllib.parse.quote(prompt)
        fallback_url = f"https://image.pollinations.ai/prompt/{encoded_fallback}?width=1024&height=1024&nologo=true"
        return {
            **state,
            "response": f"### 🎨 AI Image Generated\n\n![Generated Image]({fallback_url})\n\n📥 **[Open Image]({fallback_url})**",
            "images": [fallback_url],
            "agent": "image"
        }
