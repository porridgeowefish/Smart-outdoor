from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings
from app.features.llm.schemas import (
    ContextExtractionInput,
    ContextExtractionResult,
    ResponseGenerationInput,
    ResponseGenerationResult,
)


class AgentLLMProvider(Protocol):
    provider_name: str

    def extract_context(self, payload: ContextExtractionInput) -> ContextExtractionResult:
        raise NotImplementedError

    def generate_response(self, payload: ResponseGenerationInput) -> ResponseGenerationResult:
        raise NotImplementedError


def get_llm_provider() -> AgentLLMProvider:
    from app.features.llm.mock import MockLLMProvider
    from app.features.llm.openai_provider import OpenAILLMProvider

    settings = get_settings()
    if settings.use_mock_llm:
        return MockLLMProvider()
    if not settings.openai_api_key:
        return MockLLMProvider(provider_name="mock_missing_openai_key")
    return OpenAILLMProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
    )
