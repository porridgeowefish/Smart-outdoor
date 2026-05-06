from __future__ import annotations

from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.service import display_tags_from_manual_tags
from app.features.trip_plans.retrieval import preference_score


def advantage_tags(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    rank: int,
) -> list[str]:
    tags = display_tags_from_manual_tags(route.manual_tags or {}, limit=2)
    if rank == 1:
        tags.insert(0, "综合匹配")
    if analysis.distance_km <= 12:
        tags.append("一日友好")
    return tags[:3]


def recommendation_reason(route: RouteAsset, analysis: RouteAnalysisSnapshot) -> str:
    return (
        f"{route.name} 距离约 {analysis.distance_km:.1f} km，"
        f"累计爬升约 {analysis.elevation_gain_m:.0f} m，适合作为候选评估。"
    )


def estimated_duration(analysis: RouteAnalysisSnapshot) -> str:
    hours = analysis.distance_km / 3.2 + analysis.elevation_gain_m / 450
    return f"约 {max(1, round(hours, 1))} 小时"


def score_breakdown(route: RouteAsset, ability_and_preference_score: float) -> dict:
    return {
        "ability_score": ability_and_preference_score,
        "preference_score": preference_score(route),
        "evidence_score": 0.5,
    }


def planning_detail(route: RouteAsset, analysis: RouteAnalysisSnapshot) -> dict:
    return {
        "summary": f"{route.name} 是一条可作为本次出行候选的线路。",
        "risk_notes": ["近期路况未确认，出发前需要再次核实。"],
        "estimated_duration": estimated_duration(analysis),
    }
