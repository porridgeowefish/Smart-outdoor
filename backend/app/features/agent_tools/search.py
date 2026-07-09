from __future__ import annotations

from datetime import datetime, timezone
import re
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
    filtered_out_count: int = 0
    warnings: list[str] = Field(default_factory=list)
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
        "query": _focused_tavily_query(payload, query),
        "search_depth": payload.search_depth,
        "max_results": payload.max_results,
        "include_answer": payload.include_answer,
        "include_raw_content": False,
    }
    if payload.route_name:
        request_body["exact_match"] = True
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

    parsed_sources = _parse_tavily_sources(data, retrieved_at)
    sources = _filter_route_sources(parsed_sources, payload.route_name)[: payload.max_results]
    filtered_out_count = max(0, len(parsed_sources) - len(sources))
    answer = data.get("answer") if isinstance(data.get("answer"), str) else None
    if not sources:
        return SearchEvidence(
            status="limited",
            provider="tavily",
            query=query,
            summary=_limited_summary(payload.route_name, filtered_out_count),
            answer=None,
            sources=[],
            filtered_out_count=filtered_out_count,
            warnings=_filter_warnings(filtered_out_count),
            raw=data,
        )

    return SearchEvidence(
        status="confirmed",
        provider="tavily",
        query=query,
        summary=(
            f"Tavily 找到 {len(sources)} 条与线路名称相关的公开来源；"
            "仍需要以官方公告和出发前实时信息为准。"
        ),
        answer=answer if filtered_out_count == 0 else None,
        sources=sources,
        filtered_out_count=filtered_out_count,
        warnings=_filter_warnings(filtered_out_count),
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


def _focused_tavily_query(payload: SearchRequest, fallback_query: str) -> str:
    route_name = (payload.route_name or "").strip()
    if not route_name:
        return fallback_query
    terms = [f'"{route_name}"', "徒步", "攻略", "路况", "安全"]
    fallback_terms = [
        term
        for term in re.split(r"\s+", fallback_query)
        if term and term not in route_name and term not in {"沿途风光", "近期", "应急", "电话"}
    ]
    for term in fallback_terms:
        if term not in terms:
            terms.append(term)
    return " ".join(terms[:8])


def _filter_route_sources(
    sources: list[WebEvidenceSource],
    route_name: str | None,
) -> list[WebEvidenceSource]:
    tokens = route_match_tokens(route_name)
    if not tokens:
        return sources
    matched = [
        source
        for source in sources
        if _source_matches_route(source, tokens)
    ]
    return matched


def route_match_tokens(route_name: str | None) -> list[str]:
    name = _normalize_text(route_name)
    if not name:
        return []

    tokens: list[str] = []
    for part in re.findall(r"[\u4e00-\u9fff]+|[a-z0-9]+", name):
        if len(part) >= 2:
            tokens.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) >= 4:
            tokens.extend(part[index : index + 2] for index in range(len(part) - 1))

    generic = {
        "徒步",
        "登山",
        "爬山",
        "夜爬",
        "穿越",
        "环线",
        "一日",
        "一日游",
        "攻略",
        "路线",
        "线路",
    }
    deduped: list[str] = []
    for token in tokens:
        if token in generic or token in deduped:
            continue
        deduped.append(token)
    return deduped


def _source_matches_route(source: WebEvidenceSource, tokens: list[str]) -> bool:
    haystack = _normalize_text(f"{source.title} {source.content} {source.url}")
    return any(token in haystack for token in tokens)


def _normalize_text(value: str | None) -> str:
    return re.sub(r"[^\u4e00-\u9fffa-z0-9]+", "", (value or "").lower())


def _limited_summary(route_name: str | None, filtered_out_count: int) -> str:
    if filtered_out_count:
        label = f"“{route_name}”" if route_name else "目标线路"
        return f"Tavily 返回结果未能匹配{label}名称，已过滤；近期公开证据不足。"
    return "Tavily 已调用，但没有返回可用来源；近期公开证据不足。"


def _filter_warnings(filtered_out_count: int) -> list[str]:
    if not filtered_out_count:
        return []
    return [f"已过滤 {filtered_out_count} 条未匹配线路名称的搜索结果，避免无关内容进入 AI 摘要。"]


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
