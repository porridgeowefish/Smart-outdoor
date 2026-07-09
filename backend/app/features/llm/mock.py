from __future__ import annotations

import hashlib

from app.features.llm.schemas import (
    ContextExtractionInput,
    ContextExtractionResult,
    ResponseGenerationInput,
    ResponseGenerationResult,
)
from app.features.trip_plans.context import context_summary, update_context_state
from app.features.trip_plans.response import recommendation_content, waiting_user_content


_EMBEDDING_DIM = 256
_ACTIVE_DIMS = 4


def _deterministic_embedding(text: str) -> list[float]:
    """Sparse orthogonal embedding: same text → identical unit vector; different
    texts → near-orthogonal (cosine ≈ 0) so recall only fires on real overlap.
    Deterministic, no randomness — safe for offline tests.
    """
    vector = [0.0] * _EMBEDDING_DIM
    for index in range(_ACTIVE_DIMS):
        digest = hashlib.sha256(f"{text}|{index}".encode("utf-8")).digest()
        position = int.from_bytes(digest[:4], "big") % _EMBEDDING_DIM
        vector[position] = 1.0
    norm = sum(value * value for value in vector) ** 0.5
    if norm:
        vector = [value / norm for value in vector]
    return vector


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
        elif payload.kind == "web_evidence_summary":
            route = payload.candidate_routes[0] if payload.candidate_routes else {}
            evidence = route.get("web_evidence") if isinstance(route, dict) else {}
            sources = evidence.get("sources") if isinstance(evidence, dict) else []
            source_count = len(sources) if isinstance(sources, list) else 0
            route_name = str(route.get("route_name") or "这条线路")
            content = (
                f"{route_name} 的公开信息已检索到 {source_count} 条来源。"
                "当前摘要为 mock LLM 结果：沿途风光、近期路况和应急信息仍需以来源链接、官方公告和出发前实时信息核实。"
            )
        else:
            content = recommendation_content(candidate_count=payload.candidate_count)
        return ResponseGenerationResult(provider=self.provider_name, content=content)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_deterministic_embedding(text) for text in texts]
