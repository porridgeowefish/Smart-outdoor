from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings

SearchStatus = Literal["confirmed", "limited", "unavailable"]


class SearchRequest(BaseModel):
    query: str
    route_name: str | None = None
    max_results: int = Field(default=5, ge=1, le=10)
    search_depth: str = "basic"
    include_answer: bool = False


class WebEvidenceSource(BaseModel):
    title: str
    url: str
    content: str
    score: float | None = None
    retrieved_at: str


class SearchEvidence(BaseModel):
    status: SearchStatus
    provider: str
    query: str
    summary: str
    answer: str | None = None
    sources: list[WebEvidenceSource] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


def get_search_evidence(payload: SearchRequest) -> SearchEvidence:
    query = payload.query.strip()
    if not query:
        return SearchEvidence(
            status="unavailable",
            provider="mock",
            query=query,
            summary="搜索关键词为空，无法检索近期公开证据。",
        )

    settings = get_settings()
    if settings.use_mock_search:
        return _mock_search(payload, query)

    if not settings.tavily_api_key:
        return SearchEvidence(
            status="unavailable",
            provider="tavily",
            query=query,
            summary="未配置 Tavily API Key，近期公开证据未确认。",
        )

    return _tavily_search(payload, query, settings.tavily_api_key)


def search_evidence_json(payload: SearchRequest) -> dict[str, Any]:
    return get_search_evidence(payload).model_dump()


def _tavily_search(payload: SearchRequest, query: str, api_key: str) -> SearchEvidence:
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    request_body = {
        "query": query,
        "search_depth": payload.search_depth,
        "max_results": payload.max_results,
        "include_answer": payload.include_answer,
        "include_raw_content": False,
    }
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=request_body,
            timeout=12.0,
            trust_env=False,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500] if exc.response is not None else ""
        detail = f"{exc}; response={body}" if body else str(exc)
        return SearchEvidence(
            status="unavailable",
            provider="tavily",
            query=query,
            summary=f"Tavily 调用失败，近期公开证据未确认：{detail}",
        )
    except httpx.HTTPError as exc:
        return SearchEvidence(
            status="unavailable",
            provider="tavily",
            query=query,
            summary=f"Tavily 调用失败，近期公开证据未确认：{exc}",
        )

    sources = _parse_tavily_sources(data, retrieved_at)[: payload.max_results]
    answer = data.get("answer") if isinstance(data.get("answer"), str) else None
    if not sources:
        return SearchEvidence(
            status="limited",
            provider="tavily",
            query=query,
            summary="Tavily 已调用，但没有返回可用来源；近期公开证据不足。",
            answer=answer,
            sources=[],
            raw=data,
        )

    return SearchEvidence(
        status="confirmed",
        provider="tavily",
        query=query,
        summary=f"Tavily 找到 {len(sources)} 条公开来源；仍需要以官方公告和出发前实时信息为准。",
        answer=answer,
        sources=sources,
        raw=data,
    )


def _parse_tavily_sources(
    data: dict[str, Any],
    retrieved_at: str,
) -> list[WebEvidenceSource]:
    results = data.get("results")
    if not isinstance(results, list):
        return []
    sources = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        content = str(item.get("content") or "").strip()
        if not title or not url:
            continue
        sources.append(
            WebEvidenceSource(
                title=title,
                url=url,
                content=content,
                score=_float_or_none(item.get("score")),
                retrieved_at=retrieved_at,
            )
        )
    return sources


def _mock_search(payload: SearchRequest, query: str) -> SearchEvidence:
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    route_name = payload.route_name or "候选路线"
    source = WebEvidenceSource(
        title=f"{route_name} 公开信息检索占位",
        url="https://example.com/smart-outdoor/mock-evidence",
        content=(
            "这是 mock 搜索结果，仅用于验证 Agent 证据结构。"
            "真实近期路况、封山封路、实走记录需要接入 Tavily 后确认。"
        ),
        score=0.42,
        retrieved_at=retrieved_at,
    )
    return SearchEvidence(
        status="limited",
        provider="mock",
        query=query,
        summary="当前为 mock 搜索证据，未确认近期公开路况；出发前需要核实。",
        answer=None,
        sources=[source][: payload.max_results],
        raw={},
    )


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
