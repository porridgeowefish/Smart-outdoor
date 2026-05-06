from __future__ import annotations

from sqlalchemy.orm import Session

from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.service import display_tags_from_manual_tags, get_latest_analysis_for_route
from app.features.users.model import User, UserAbilityProfile


def retrieve_visible_routes(
    db: Session,
    current_user: User,
) -> list[tuple[RouteAsset, RouteAnalysisSnapshot, float]]:
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
        score = ability_score(analysis, ability) + preference_score(route)
        ranked.append((route, analysis, round(min(score, 1.0), 4)))
    ranked.sort(key=lambda item: item[2], reverse=True)
    return ranked


def ability_score(
    analysis: RouteAnalysisSnapshot,
    ability: UserAbilityProfile | None,
) -> float:
    if ability is None or ability.recent_max_distance_km is None:
        return 0.55
    distance_ratio = analysis.distance_km / max(ability.recent_max_distance_km, 1)
    climb_ratio = analysis.elevation_gain_m / max(
        ability.recent_max_elevation_gain_m or 300,
        1,
    )
    penalty = max(distance_ratio - 1.2, 0) * 0.2 + max(climb_ratio - 1.2, 0) * 0.3
    return max(0.1, 0.75 - penalty)


def preference_score(route: RouteAsset) -> float:
    tags = set(display_tags_from_manual_tags(route.manual_tags or {}, limit=10))
    score = 0.2
    if "雪山" in tags:
        score += 0.15
    if "自驾" in tags:
        score += 0.05
    return score


def _user_ability_profile(db: Session, current_user: User) -> UserAbilityProfile | None:
    return (
        db.query(UserAbilityProfile)
        .filter(UserAbilityProfile.user_id == current_user.id)
        .first()
    )
