from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.service import get_latest_analysis_for_route
from app.features.routes.tag_taxonomy import context_preference_tags, route_tags
from app.features.users.model import User, UserAbilityProfile


@dataclass(frozen=True)
class RouteScore:
    total: float
    ability: float
    preference: float
    metrics: float
    evidence: float
    matched_tags: list[str]
    route_tags: list[str]


def retrieve_visible_routes(
    db: Session,
    current_user: User,
    context_state: dict | None = None,
) -> list[tuple[RouteAsset, RouteAnalysisSnapshot, RouteScore]]:
    context_state = context_state or {}
    ability = _user_ability_profile(db, current_user)
    routes = (
        db.query(RouteAsset)
        .filter(RouteAsset.status == "active")
        .order_by(RouteAsset.created_at.desc())
        .all()
    )
    ranked = []
    for route in routes:
        if route.visibility != "public" and route.created_by_user_id != current_user.id:
            continue
        analysis = get_latest_analysis_for_route(db, route.id)
        if analysis is None:
            continue
        score = score_route(route, analysis, ability, context_state)
        ranked.append((route, analysis, score))
    ranked.sort(key=lambda item: item[2].total, reverse=True)
    return ranked


def score_route(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    ability: UserAbilityProfile | None,
    context_state: dict | None = None,
) -> RouteScore:
    context_state = context_state or {}
    ability_component = ability_fit_score(analysis, ability, context_state)
    preference_component, matched_tags, tags = preference_score(route, analysis, context_state)
    metrics_component = metric_quality_score(analysis)
    evidence_component = 0.08
    total = min(
        1.0,
        ability_component + preference_component + metrics_component + evidence_component,
    )
    return RouteScore(
        total=round(total, 4),
        ability=round(ability_component, 4),
        preference=round(preference_component, 4),
        metrics=round(metrics_component, 4),
        evidence=round(evidence_component, 4),
        matched_tags=matched_tags,
        route_tags=sorted(tags),
    )


def ability_fit_score(
    analysis: RouteAnalysisSnapshot,
    ability: UserAbilityProfile | None,
    context_state: dict | None = None,
) -> float:
    context_state = context_state or {}
    target = _target_capacity(ability, context_state)
    distance_ratio = analysis.distance_km / max(target["distance_km"], 1)
    climb_ratio = analysis.elevation_gain_m / max(target["elevation_gain_m"], 1)

    over_penalty = max(distance_ratio - 1.0, 0) * 0.22 + max(climb_ratio - 1.0, 0) * 0.34
    under_penalty = max(0.45 - distance_ratio, 0) * 0.08 + max(0.35 - climb_ratio, 0) * 0.08
    score = 0.48 - over_penalty - under_penalty
    if ability and ability.confidence == "high":
        score += 0.04
    if ability is None:
        score -= 0.05
    return max(0.05, min(score, 0.52))


def preference_score(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict | None = None,
) -> tuple[float, list[str], set[str]]:
    tags = route_tags(route, analysis)
    wanted = context_preference_tags(context_state or {})
    if not wanted:
        return 0.12, [], tags
    matched = sorted(tags.intersection(wanted))
    score = 0.10 + min(len(matched) * 0.055, 0.28)
    avoid_tags = set()
    avoid_raw = (context_state or {}).get("avoid_tags")
    if isinstance(avoid_raw, list):
        avoid_tags = {str(item) for item in avoid_raw}
    if avoid_tags.intersection(tags):
        score -= 0.12
    return max(0.0, min(score, 0.32)), matched, tags


def metric_quality_score(analysis: RouteAnalysisSnapshot) -> float:
    score = 0.08
    if analysis.distance_km > 0 and analysis.elevation_gain_m >= 0:
        score += 0.05
    if analysis.center_point and analysis.start_point and analysis.end_point:
        score += 0.04
    if analysis.track_geojson and analysis.track_geojson.get("coordinates"):
        score += 0.03
    return min(score, 0.20)


def _target_capacity(
    ability: UserAbilityProfile | None,
    context_state: dict,
) -> dict[str, float]:
    if ability and ability.recent_max_distance_km:
        distance = max(ability.recent_max_distance_km, 6)
        climb = max(ability.recent_max_elevation_gain_m or 300, 250)
    else:
        distance = 12
        climb = 600

    hint = context_state.get("ability_hint")
    level = hint.get("level") if isinstance(hint, dict) else None
    if level == "beginner":
        distance *= 0.75
        climb *= 0.65
    elif level == "normal":
        distance *= 0.95
        climb *= 0.9
    elif level == "strong":
        distance *= 1.15
        climb *= 1.2

    metrics = ability.metrics_json if ability and isinstance(ability.metrics_json, dict) else {}
    if metrics.get("max_vertical_speed_m_per_h"):
        climb *= min(max(float(metrics["max_vertical_speed_m_per_h"]) / 500, 0.8), 1.35)

    return {"distance_km": distance, "elevation_gain_m": climb}


def _user_ability_profile(db: Session, current_user: User) -> UserAbilityProfile | None:
    return (
        db.query(UserAbilityProfile)
        .filter(UserAbilityProfile.user_id == current_user.id)
        .first()
    )
