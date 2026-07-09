from __future__ import annotations

from types import SimpleNamespace

from app.features.trip_plans.context import (
    context_summary,
    confirmed_context,
    display_context_value,
    geocode_location,
    geo_raw_text,
    merge_choice_answers,
    merge_text_context_state,
    missing_context_fields,
    update_context_state,
)
from app.features.trip_plans.evaluation import estimated_duration, recommendation_reason
from app.features.trip_plans.evidence import candidate_evidence, summarize_web_evidence


def test_context_update_extracts_current_rule_based_constraints() -> None:
    state = update_context_state(
        {},
        "周末从成都出发，自驾，一天往返，看雪山，中等强度",
    )

    assert state["departure_area"] == "成都"
    assert state["activity_goal"] == "看雪山"
    assert state["transport_hint"] == "self_drive"
    assert state["time_window"]["duration_days"] == 1
    assert state["ability_hint"]["level"] == "normal"
    assert context_summary(state, "fallback") == "从成都出发，看雪山，自驾，中等强度"


def test_choice_answers_write_whitelisted_context_with_user_choice_source() -> None:
    state = merge_choice_answers(
        {"transport_hint": "public_transport", "field_sources": {"transport_hint": "ai_extracted"}},
        [
            {
                "field": "transport_hint",
                "value": "self_drive",
                "label": "自驾",
                "custom_text": None,
            }
        ],
    )

    assert state["transport_hint"] == "self_drive"
    assert state["field_sources"]["transport_hint"] == "user_choice"
    assert state["confirmed_fields"] == ["transport_hint"]
    assert confirmed_context(state)["items"] == [
        {"field": "transport_hint", "label": "交通", "value": "自驾"}
    ]


def test_missing_context_fields_uses_scenario_based_risk_fields() -> None:
    state = {
        "activity_goal": "看雪山",
        "departure_area": "成都",
        "time_window": {"raw_text": "周末"},
        "transport_hint": "self_drive",
    }

    assert missing_context_fields(state) == ["terrain_tolerance"]


def test_evaluation_keeps_candidate_reason_grounded_in_route_metrics() -> None:
    route = SimpleNamespace(name="测试线路")
    analysis = SimpleNamespace(distance_km=12.4, elevation_gain_m=560)

    assert "12.4 km" in recommendation_reason(route, analysis)
    assert "560 m" in recommendation_reason(route, analysis)
    assert estimated_duration(analysis) == "约 5.1 小时"


def test_candidate_evidence_returns_weather_transport_and_web_sources(monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_WEATHER", "true")
    monkeypatch.setenv("USE_MOCK_AMAP", "true")
    monkeypatch.setenv("USE_MOCK_SEARCH", "true")
    route = SimpleNamespace(
        name="测试线路",
        manual_tags={"location": ["成都"]},
    )
    analysis = SimpleNamespace(
        center_point={"lon": 104.06, "lat": 30.67},
        analysis_json={"location": {"city": "成都市", "display_name": "四川省 · 成都市"}},
        distance_km=12.4,
    )

    evidence = candidate_evidence(
        route,
        analysis,
        {"departure_area": "成都", "transport_hint": "self_drive", "activity_goal": "徒步"},
    )

    assert evidence["weather"]["status"] == "mocked"
    assert evidence["transport"]["preferred_mode"] == "self_drive"
    assert evidence["web_evidence"]["provider"] == "mock"
    assert evidence["web_evidence"]["sources"][0]["url"]
    assert "测试线路 已筛出" in evidence["web_evidence"]["summary"]
    assert evidence["web_evidence"]["summary_provider"] == "deterministic_fallback"


def test_web_evidence_summary_keeps_compact_fallback_when_llm_returns_source_dump() -> None:
    class DumpingProvider:
        provider_name = "dumping"

        def generate_response(self, payload):
            return SimpleNamespace(
                provider="dumping",
                content="# 黄连盂 #徒步 " * 80 + "Please login before leaving comments",
            )

    route = SimpleNamespace(name="黄连盂")
    analysis = SimpleNamespace(distance_km=10.0, elevation_gain_m=800)
    web_evidence = {
        "status": "confirmed",
        "summary": "Tavily 找到 2 条与线路名称相关的公开来源。",
        "sources": [
            {
                "title": "黄连盂夜爬攻略",
                "url": "https://example.com/a",
                "content": "黄连盂海拔1818米，全程约10公里，部分来源提醒不适合新手。",
            },
            {
                "title": "黄连盂徒步记录",
                "url": "https://example.com/b",
                "content": "路线涉及山路，建议出发前核实天气和当地管理信息。",
            },
        ],
    }

    result = summarize_web_evidence(route, analysis, {}, web_evidence, DumpingProvider())

    assert result["summary_provider"] == "deterministic_fallback"
    assert len(result["summary"]) < 360
    assert "Please login" not in result["summary"]
    assert "AI 摘要过长" in result["warnings"][0]


def test_geocode_location_returns_structured_dict_when_geocoder_succeeds() -> None:
    fake_coord = SimpleNamespace(lon=104.065735, lat=30.659462)

    result = geocode_location("成都", geocoder=lambda _addr: fake_coord)

    assert result == {"raw_text": "成都", "lat": 30.659462, "lng": 104.065735}


def test_geocode_location_degrades_to_none_when_geocoder_returns_none() -> None:
    result = geocode_location("未知地名", geocoder=lambda _addr: None)

    assert result == {"raw_text": "未知地名", "lat": None, "lng": None}


def test_geocode_location_degrades_when_no_geocoder_injected() -> None:
    result = geocode_location("深圳")

    assert result == {"raw_text": "深圳", "lat": None, "lng": None}


def test_display_context_value_renders_current_location_raw_text() -> None:
    value = {"raw_text": "深圳", "lat": 22.5431, "lng": 114.0579}

    assert display_context_value("current_location", value) == "深圳"


def test_merge_choice_answers_accepts_current_location_field() -> None:
    state = merge_choice_answers(
        {},
        [
            {
                "field": "current_location",
                "value": "shenzhen",
                "label": "深圳",
                "custom_text": None,
            }
        ],
    )

    assert state["current_location"] == "shenzhen"
    assert state["confirmed_fields"] == ["current_location"]


def test_confirmed_context_renders_current_location_label() -> None:
    state = {
        "current_location": {"raw_text": "深圳", "lat": 22.5431, "lng": 114.0579},
        "confirmed_fields": ["current_location"],
    }

    assert confirmed_context(state)["items"] == [
        {"field": "current_location", "label": "当前位置", "value": "深圳"}
    ]


def test_geo_raw_text_handles_dict_str_and_none() -> None:
    assert geo_raw_text({"raw_text": "成都", "lat": 30.6, "lng": 104.0}) == "成都"
    assert geo_raw_text("深圳") == "深圳"
    assert geo_raw_text(None) is None


def test_merge_text_context_state_structures_departure_area() -> None:
    merged = merge_text_context_state(
        {},
        {"departure_area": "成都"},
        "周末从成都出发",
    )

    assert merged["departure_area"] == {"raw_text": "成都", "lat": None, "lng": None}


def test_context_summary_renders_structured_departure_area() -> None:
    state = {"departure_area": {"raw_text": "成都", "lat": 30.6, "lng": 104.0}}

    assert context_summary(state, "fallback") == "从成都出发"


def test_display_context_value_renders_departure_area_raw_text() -> None:
    value = {"raw_text": "成都", "lat": 30.6, "lng": 104.0}

    assert display_context_value("departure_area", value) == "成都"
