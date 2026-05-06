from __future__ import annotations

from app.features.llm.schemas import (
    ContextExtractionInput,
    ContextExtractionResult,
    ResponseGenerationInput,
    ResponseGenerationResult,
)
from app.features.trip_plans.context import context_summary, update_context_state
from app.features.trip_plans.response import recommendation_content, waiting_user_content


class MockLLMProvider:
    def __init__(self, provider_name: str = "mock") -> None:
        self.provider_name = provider_name

    def extract_context(self, payload: ContextExtractionInput) -> ContextExtractionResult:
        context_state = update_context_state(
            payload.existing_context_state,
            payload.content,
        )
        return ContextExtractionResult(
            provider=self.provider_name,
            context_state=context_state,
            context_summary=context_summary(context_state, payload.content),
            confidence=0.6,
        )

    def generate_response(self, payload: ResponseGenerationInput) -> ResponseGenerationResult:
        if payload.kind == "waiting_user":
            content = waiting_user_content()
        elif payload.kind == "candidate_detail_card":
            route_name = (
                payload.candidate_routes[0].get("route_name", "这条路线")
                if payload.candidate_routes
                else "这条路线"
            )
            content = (
                f"{route_name} 可以作为本次候选，但当前详情卡片使用 mock LLM 文案。"
                "请重点看卡片里的天气、交通和公开来源证据；未确认的信息需要出发前复核。"
            )
        else:
            content = recommendation_content(candidate_count=payload.candidate_count)
        return ResponseGenerationResult(provider=self.provider_name, content=content)
