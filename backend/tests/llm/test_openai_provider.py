from __future__ import annotations

import json
from types import SimpleNamespace

from app.features.llm.openai_provider import OpenAILLMProvider
from app.features.llm.schemas import ContextExtractionInput, ResponseGenerationInput


class _FakeChatCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.last_payload = None

    def create(self, **payload):
        self.last_payload = payload
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content),
                )
            ]
        )


class _FakeOpenAIClient:
    def __init__(self, content: str) -> None:
        self.completions = _FakeChatCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


def test_openai_provider_extracts_context_from_json_response() -> None:
    client = _FakeOpenAIClient(
        json.dumps(
            {
                "context_state": {
                    "departure_area": "成都",
                    "activity_goal": "徒步",
                    "transport_hint": "self_drive",
                },
                "context_summary": "用户想从成都出发，自驾徒步。",
                "confidence": 0.78,
            },
            ensure_ascii=False,
        )
    )
    provider = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://example.com/v1",
        client=client,
    )

    result = provider.extract_context(
        ContextExtractionInput(
            existing_context_state={"time_window": {"duration_days": 1}},
            content="奇葩输入：我想出去发疯但最好成都周边自驾徒步",
        )
    )

    payload = client.completions.last_payload
    assert payload["model"] == "test-model"
    assert payload["response_format"] == {"type": "json_object"}
    assert "奇葩输入" in payload["messages"][-1]["content"]
    assert result.provider == "openai"
    assert result.context_state["departure_area"] == "成都"
    assert result.context_state["transport_hint"] == "self_drive"
    assert result.context_state["time_window"]["duration_days"] == 1
    assert result.confidence == 0.78


def test_openai_provider_falls_back_to_mock_on_invalid_json() -> None:
    provider = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://example.com/v1",
        client=_FakeOpenAIClient("not-json"),
    )

    result = provider.extract_context(
        ContextExtractionInput(existing_context_state={}, content="成都周末自驾看雪山")
    )

    assert result.provider == "mock_fallback"
    assert result.context_state["departure_area"] == "成都"
    assert result.context_state["activity_goal"] == "看雪山"


def test_openai_provider_generates_natural_response_with_workflow_payload() -> None:
    client = _FakeOpenAIClient("我按你这次的偏好先整理了 3 条候选，点开卡片可以看证据。")
    provider = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://example.com/v1",
        client=client,
    )

    result = provider.generate_response(
        ResponseGenerationInput(
            kind="recommendation",
            context_state={"departure_area": "成都"},
            candidate_count=3,
            candidate_routes=[{"name": "线路 A"}],
        )
    )

    payload = client.completions.last_payload
    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.6
    assert "线路 A" in payload["messages"][-1]["content"]
    assert result.provider == "openai"
    assert "3 条候选" in result.content
