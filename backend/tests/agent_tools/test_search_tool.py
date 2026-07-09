from __future__ import annotations

from types import SimpleNamespace


def test_search_tool_mock_returns_tavily_aligned_sources(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=True, tavily_api_key=None),
    )

    result = search.get_search_evidence(
        search.SearchRequest(
            query="四姑娘山 近期 路况 徒步",
            route_name="四姑娘山大峰",
            max_results=3,
        )
    )

    assert result.status == "limited"
    assert result.provider == "mock"
    assert result.query == "四姑娘山 近期 路况 徒步"
    assert len(result.sources) == 1
    source = result.sources[0]
    assert source.title
    assert source.url.startswith("https://")
    assert source.content
    assert source.score is not None
    assert source.retrieved_at
    assert result.raw == {}


def test_search_tool_empty_query_degrades(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=True, tavily_api_key=None),
    )

    result = search.get_search_evidence(search.SearchRequest(query="   "))

    assert result.status == "unavailable"
    assert result.provider == "mock"
    assert result.sources == []


def test_search_tool_real_tavily_parses_sources(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=False, tavily_api_key="test-key"),
    )
    calls = []

    def fake_post(url: str, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(
            {
                "answer": "近期公开信息需要出发前复核。",
                "results": [
                    {
                        "title": "景区公告",
                        "url": "https://example.com/notice",
                        "content": "景区道路维护公告。",
                        "score": 0.91,
                    }
                ],
            }
        )

    monkeypatch.setattr(search.httpx, "post", fake_post)

    result = search.get_search_evidence(
        search.SearchRequest(query="路线 近期路况", include_answer=True)
    )

    assert result.status == "confirmed"
    assert result.provider == "tavily"
    assert result.answer == "近期公开信息需要出发前复核。"
    assert result.sources[0].title == "景区公告"
    assert calls[0][0] == "https://api.tavily.com/search"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0][1]["json"]["query"] == "路线 近期路况"


def test_search_tool_filters_results_that_do_not_match_route_name(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=False, tavily_api_key="test-key"),
    )

    def fake_post(url: str, **kwargs):
        return FakeResponse(
            {
                "answer": "梅沙尖云海和当餐食材推荐混在一起。",
                "results": [
                    {
                        "title": "梧桐山夜爬攻略：登山路线与下撤提醒",
                        "url": "https://example.com/wutongshan",
                        "content": "梧桐山夜爬需要关注天气和公园公告。",
                        "score": 0.93,
                    },
                    {
                        "title": "梅沙尖云海一日游攻略",
                        "url": "https://example.com/meishajian",
                        "content": "梅沙尖登山路线与云海观景点。",
                        "score": 0.88,
                    },
                    {
                        "title": "当餐食材供应链推荐",
                        "url": "https://example.com/food",
                        "content": "食材、餐饮、供应链。",
                        "score": 0.80,
                    },
                ],
            }
        )

    monkeypatch.setattr(search.httpx, "post", fake_post)

    result = search.get_search_evidence(
        search.SearchRequest(
            query="梧桐山夜爬 深圳 徒步 攻略 路况 安全",
            route_name="梧桐山夜爬",
            include_answer=True,
        )
    )

    assert result.status == "confirmed"
    assert [source.title for source in result.sources] == [
        "梧桐山夜爬攻略：登山路线与下撤提醒"
    ]
    assert result.answer is None
    assert result.filtered_out_count == 2
    assert result.warnings


def test_search_tool_degrades_when_all_results_miss_route_name(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=False, tavily_api_key="test-key"),
    )

    def fake_post(url: str, **kwargs):
        return FakeResponse(
            {
                "answer": "完全无关的搜索摘要。",
                "results": [
                    {
                        "title": "梅沙尖云海一日游攻略",
                        "url": "https://example.com/meishajian",
                        "content": "梅沙尖路线。",
                        "score": 0.88,
                    }
                ],
            }
        )

    monkeypatch.setattr(search.httpx, "post", fake_post)

    result = search.get_search_evidence(
        search.SearchRequest(
            query="梧桐山夜爬 深圳 徒步 攻略 路况 安全",
            route_name="梧桐山夜爬",
            include_answer=True,
        )
    )

    assert result.status == "limited"
    assert result.sources == []
    assert result.answer is None
    assert "已过滤" in result.warnings[0]


def test_search_tool_focuses_route_query_with_exact_match(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=False, tavily_api_key="test-key"),
    )
    calls = []

    def fake_post(url: str, **kwargs):
        calls.append(kwargs["json"])
        return FakeResponse(
            {
                "results": [
                    {
                        "title": "梧桐山夜爬攻略",
                        "url": "https://example.com/wutongshan",
                        "content": "梧桐山夜爬路线。",
                        "score": 0.9,
                    }
                ],
            }
        )

    monkeypatch.setattr(search.httpx, "post", fake_post)

    search.get_search_evidence(
        search.SearchRequest(
            query="梧桐山夜爬 深圳 徒步 沿途风光 近期 路况 安全 应急 电话",
            route_name="梧桐山夜爬",
        )
    )

    assert calls[0]["query"].startswith('"梧桐山夜爬" 徒步 攻略 路况 安全')
    assert calls[0]["exact_match"] is True


def test_search_tool_real_provider_missing_key_degrades(monkeypatch) -> None:
    from app.features.agent_tools import search

    monkeypatch.setattr(
        search,
        "get_settings",
        lambda: SimpleNamespace(use_mock_search=False, tavily_api_key=None),
    )

    result = search.get_search_evidence(search.SearchRequest(query="路线 近期路况"))

    assert result.status == "unavailable"
    assert result.provider == "tavily"
    assert result.sources == []


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload
