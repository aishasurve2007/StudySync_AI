"""
Picks the AI provider from config. One env var (AI_PROVIDER) swaps the
backend; a missing key transparently falls back to NullProvider so the app
always boots. Exposed as a FastAPI dependency so tests can override it with
a fake provider.
"""
from functools import lru_cache

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.providers import GeminiProvider, NullProvider, OpenAIProvider


@lru_cache
def _build_provider() -> AIProvider:
    provider = (settings.AI_PROVIDER or "none").lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(settings.GEMINI_API_KEY)
    return NullProvider()


def get_ai_provider() -> AIProvider:
    return _build_provider()
