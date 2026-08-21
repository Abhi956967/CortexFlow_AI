import os
import logging
from typing import List, Any
from app.core.config import settings

logger = logging.getLogger("cortexflow")

def extract_text_content(content: Any) -> str:
    """
    Safely extract plain text string from model response content (str or list of parts).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", str(item)))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content or "")

def get_model(agent_type: str = "chat", streaming: bool = False):
    """
    Returns a lightning-fast LangChain ChatModel with automatic multi-provider fallback.
    Prioritizes Groq (1.4s ultra-fast inference) and falls back to Gemini & OpenAI.
    """
    candidate_models: List[Any] = []
    temperature = 0.7 if agent_type == "chat" else 0.2

    # 1. Groq (Ultra-fast LPU inference)
    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if groq_key and len(groq_key) > 10:
        groq_models = ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b", "groq/compound"]
        for g_model in groq_models:
            try:
                from langchain_groq import ChatGroq
                groq_inst = ChatGroq(
                    api_key=groq_key,
                    model_name=g_model,
                    temperature=temperature,
                    max_retries=0,
                    timeout=8.0
                )
                candidate_models.append(groq_inst)
            except Exception as e:
                logger.warning(f"Could not init Groq {g_model}: {e}")

    # 2. Google Gemini Models (Fast flash backup)
    google_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_key and len(google_key) > 10:
        gemini_model_names = [
            "gemini-flash-latest",
            "gemini-3.6-flash",
            "gemini-3.5-flash"
        ]
        for g_model in gemini_model_names:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model_inst = ChatGoogleGenerativeAI(
                    google_api_key=google_key,
                    model=g_model,
                    temperature=temperature,
                    streaming=streaming,
                    max_retries=0,
                    timeout=8.0
                )
                candidate_models.append(model_inst)
            except Exception as e:
                logger.warning(f"Could not init Gemini model {g_model}: {e}")

    # 3. OpenAI Models (Backup)
    openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        try:
            from langchain_openai import ChatOpenAI
            model_name = "gpt-4o" if agent_type in ["coding", "ppt", "pdf"] else "gpt-4o-mini"
            openai_inst = ChatOpenAI(
                api_key=openai_key,
                model=model_name,
                temperature=temperature,
                streaming=streaming,
                max_retries=0,
                timeout=8.0
            )
            candidate_models.append(openai_inst)
        except Exception as e:
            logger.warning(f"Could not init OpenAI: {e}")

    if not candidate_models:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=openai_key or "sk-dummy-key-for-local-init",
            model="gpt-4o-mini",
            temperature=temperature
        )

    if len(candidate_models) == 1:
        return candidate_models[0]

    # Return Primary model with instant fallbacks
    primary_model = candidate_models[0]
    fallback_models = candidate_models[1:]
    return primary_model.with_fallbacks(fallback_models)
