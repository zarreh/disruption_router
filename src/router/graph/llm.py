"""LLM client factory for the router graph."""

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from router.settings import get_settings


def get_llm(temperature: float = 0.0) -> ChatOpenAI | None:
    """Return a configured ChatOpenAI client, or None if no API key is set."""
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        api_key=SecretStr(settings.openai_api_key),
    )
