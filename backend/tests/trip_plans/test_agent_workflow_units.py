from __future__ import annotations

from types import SimpleNamespace

from app.features.trip_plans.context import context_summary, update_context_state
from app.features.trip_plans.evaluation import estimated_duration, recommendation_reason
from app.features.trip_plans.evidence import candidate_evidence


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
