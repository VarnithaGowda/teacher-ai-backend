"""
ai_services/gemini_client.py - Gemini LLM client using LangChain
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
import logging

logger = logging.getLogger(__name__)

_llm_cache = {}


def get_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    global _llm_cache
    if temperature not in _llm_cache:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        _llm_cache[temperature] = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )
    return _llm_cache[temperature]


async def generate_text(prompt: str, temperature: float = 0.7) -> str:
    try:
        llm = get_llm(temperature)
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        raise