from __future__ import annotations

from types import SimpleNamespace

from app.features.routes.tag_taxonomy import all_taxonomy_tags, context_preference_tags
from app.features.trip_plans.retrieval import ability_fit_score, preference_score


def test_tag_taxonomy_has_enough_detailed_categories() -> None:
    tags = all_taxonomy_tags()

    assert len(set(tags)) >= 30
    assert {"有小卖部", "停车场", "台阶路/阶梯路", "雪山", "摄影友好"}.issubset(set(tags))


def test_context_preference_tags_extracts_user_intent() -> None:
    tags = context_preference_tags(
        {
            "activity_goal": "想徒步看雪山，最好能拍照出片",
            "transport_hint": "自驾，最好有停车场",
            "ability_hint": {"level": "beginner", "raw_text": "轻松一点"},
            "time_window": {"raw_text": "周末一天"},
        }
    )

    assert {"雪山", "摄影友好", "自驾友好", "停车场"}.issubset(tags)


def test_preference_score_rewards_matching_tags() -> None:
    route = SimpleNamespace(
        manual_tags={
            "scenery": ["雪山"],
            "audience": ["摄影友好"],
            "transport_facility": ["停车场"],
        }
    )
    analysis = SimpleNamespace(distance_km=10, elevation_gain_m=400)

    score, matched, tags = preference_score(
        route,
        analysis,
        {"activity_goal": "想看雪山并且拍照", "transport_hint": "自驾停车方便"},
    )

    assert score > 0.18
    assert {"雪山", "摄影友好", "停车场"}.intersection(matched)
    assert "中线" in tags


def test_ability_fit_penalizes_routes_beyond_user_capacity() -> None:
    easy = SimpleNamespace(distance_km=8, elevation_gain_m=300)
    hard = SimpleNamespace(distance_km=28, elevation_gain_m=1800)
    ability = SimpleNamespace(
        recent_max_distance_km=12,
        recent_max_elevation_gain_m=700,
        confidence="high",
        metrics_json={"max_vertical_speed_m_per_h": 450},
    )

    easy_score = ability_fit_score(easy, ability, {"ability_hint": {"level": "normal"}})
    hard_score = ability_fit_score(hard, ability, {"ability_hint": {"level": "normal"}})

    assert easy_score > hard_score
