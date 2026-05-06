from __future__ import annotations

from app.features.llm.mock import MockLLMProvider
from app.features.llm.openai_provider import OpenAILLMProvider
from app.features.llm.provider import get_llm_provider
from app.features.llm.schemas import ContextExtractionInput, ResponseGenerationInput


def test_mock_llm_provider_extracts_context_with_stable_schema() -> None:
    provider = MockLLMProvider()

    result = provider.extract_context(
        ContextExtractionInput(
            existing_context_state={},
            content="周末从成都出发，自驾，一天往返，看雪山，中等强度",
        )
    )

    assert result.provider == "mock"
    assert result.context_state["departure_area"] == "成都"
    assert result.context_state["activity_goal"] == "看雪山"
    assert result.context_state["transport_hint"] == "self_drive"
    assert result.context_summary == "从成都出发，看雪山，自驾，中等强度"


def test_mock_llm_provider_generates_waiting_and_recommendation_responses() -> None:
    provider = MockLLMProvider()

    waiting = provider.generate_response(
        ResponseGenerationInput(kind="waiting_user", context_state={})
    )
    recommendation = provider.generate_response(
        ResponseGenerationInput(
            kind="recommendation",
            context_state={"departure_area": "成都"},
            candidate_count=3,
        )
    )

    assert waiting.provider == "mock"
    assert "交通方式" in waiting.content
    assert recommendation.provider == "mock"
    assert "3 条候选" in recommendation.content


def test_llm_provider_factory_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "true")

    provider = get_llm_provider()

    assert isinstance(provider, MockLLMProvider)


def test_llm_provider_factory_returns_openai_provider_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")

    provider = get_llm_provider()

    assert isinstance(provider, OpenAILLMProvider)


def test_llm_provider_factory_falls_back_without_key(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("SMART_OUTDOOR_ENV_FILE", "__missing_env_file__")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = get_llm_provider()

    assert isinstance(provider, MockLLMProvider)
    assert provider.provider_name == "mock_missing_openai_key"
