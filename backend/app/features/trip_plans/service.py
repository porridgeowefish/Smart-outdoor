from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.router import _route_location
from app.features.routes.service import display_tags_from_manual_tags, get_latest_analysis_for_route
from app.features.trip_plans.model import (
    AgentRun,
    TripPlan,
    TripPlanCandidateRoute,
    TripPlanMessage,
)
from app.features.trip_plans.schemas import (
    CandidateRouteDetailResponse,
    CandidateRouteItem,
    CandidateRouteSummary,
    TripPlanMessagePostResponse,
    TripPlanMessageResponse,
)
from app.features.users.model import User, UserAbilityProfile


class TripPlanNotFoundError(Exception):
    pass


class TripPlanClosedError(Exception):
    pass


class AgentRunNotFoundError(Exception):
    pass


class CandidateRouteNotFoundError(Exception):
    pass


def handle_user_message(
    db: Session,
    current_user: User,
    *,
    content: str,
    trip_plan_id: str | None,
) -> TripPlanMessagePostResponse:
    trip_plan = _get_or_create_trip_plan(db, current_user, content, trip_plan_id)
    if trip_plan.status == "closed":
        raise TripPlanClosedError

    user_message = TripPlanMessage(
        trip_plan_id=trip_plan.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    db.flush()

    agent_run = AgentRun(
        trip_plan_id=trip_plan.id,
        user_message_id=user_message.id,
        run_status="running",
        events_json=[],
    )
    db.add(agent_run)
    db.flush()

    context_state = _updated_context_state(trip_plan.context_state or {}, content)
    trip_plan.context_state = context_state
    trip_plan.context_summary = _context_summary(context_state, content)
    db.add(trip_plan)

    if _is_sufficient(db, trip_plan, context_state):
        assistant_content, candidates, events = _run_mock_recommendation(
            db, current_user, trip_plan, agent_run
        )
        agent_run.run_status = "succeeded"
    else:
        candidates = []
        assistant_content = (
            "我先确认两个关键信息：交通方式你更倾向自驾还是公共交通？"
            "这次想轻松一点，还是接受中等强度？"
        )
        events = [
            _event("run.phase_changed", {"phase": "sufficiency_check"}),
            _event("message.delta", {"content": assistant_content}),
            _event("message.completed", {"content": assistant_content}),
            _event("run.waiting_user", {"missing_fields": ["transport_hint", "ability_hint"]}),
            _event("run.completed", {"status": "waiting_user"}),
        ]
        agent_run.run_status = "waiting_user"

    assistant_message = TripPlanMessage(
        trip_plan_id=trip_plan.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_message)
    agent_run.events_json = events
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)
    db.refresh(user_message)
    db.refresh(assistant_message)

    return TripPlanMessagePostResponse(
        trip_plan_id=trip_plan.id,
        user_message_id=user_message.id,
        assistant_message=TripPlanMessageResponse(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
        ),
        agent_run_id=agent_run.id,
        run_status=agent_run.run_status,
        candidate_routes=[_candidate_item(db, candidate) for candidate in candidates],
    )


def get_agent_run_events(db: Session, current_user: User, agent_run_id: str) -> list[dict]:
    agent_run = db.get(AgentRun, agent_run_id)
    if agent_run is None:
        raise AgentRunNotFoundError
    trip_plan = db.get(TripPlan, agent_run.trip_plan_id)
    if trip_plan is None or trip_plan.user_id != current_user.id:
        raise AgentRunNotFoundError
    return agent_run.events_json or []


def get_candidate_detail(
    db: Session,
    current_user: User,
    trip_plan_id: str,
    candidate_id: str,
) -> CandidateRouteDetailResponse:
    trip_plan = db.get(TripPlan, trip_plan_id)
    if trip_plan is None or trip_plan.user_id != current_user.id:
        raise CandidateRouteNotFoundError
    candidate = db.get(TripPlanCandidateRoute, candidate_id)
    if candidate is None or candidate.trip_plan_id != trip_plan_id:
        raise CandidateRouteNotFoundError
    item = _candidate_item(db, candidate)
    return CandidateRouteDetailResponse(
        candidate_id=item.candidate_id,
        rank=item.rank,
        route=item.route,
        advantage_tags=item.advantage_tags,
        recommendation_reason=item.recommendation_reason,
        score_breakdown=item.score_breakdown,
        planning_detail=candidate.planning_detail or {},
        evidence=candidate.evidence or {},
    )


def sse_lines(events: list[dict]) -> str:
    chunks = []
    for event in events:
        chunks.append(f"event: {event['event']}\n")
        chunks.append(f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n")
    return "".join(chunks)


def _get_or_create_trip_plan(
    db: Session,
    current_user: User,
    content: str,
    trip_plan_id: str | None,
) -> TripPlan:
    if trip_plan_id:
        trip_plan = db.get(TripPlan, trip_plan_id)
        if trip_plan is None or trip_plan.user_id != current_user.id:
            raise TripPlanNotFoundError
        return trip_plan

    title = content.strip()[:40] or "新的出行规划"
    trip_plan = TripPlan(
        user_id=current_user.id,
        title=title,
        status="draft",
        context_summary="",
        context_state={},
    )
    db.add(trip_plan)
    db.flush()
    return trip_plan


def _updated_context_state(context_state: dict, content: str) -> dict:
    state = dict(context_state or {})
    lowered = content.lower()
    if "雪山" in content:
        state["activity_goal"] = "看雪山"
    elif "徒步" in content or "走走" in content:
        state.setdefault("activity_goal", "徒步")
    if "成都" in content:
        state["departure_area"] = "成都"
    if "自驾" in content:
        state["transport_hint"] = "self_drive"
    elif "公共交通" in content:
        state["transport_hint"] = "public_transport"
    if "一天" in content or "一日" in content or "周末" in content:
        state["time_window"] = {"raw_text": "一日或周末", "duration_days": 1}
    if "轻松" in content:
        state["ability_hint"] = {"level": "beginner"}
    elif "中等" in content or "中等强度" in content:
        state["ability_hint"] = {"level": "normal"}
    elif "挑战" in content or "强度" in lowered:
        state["ability_hint"] = {"level": "strong"}
    return state


def _context_summary(context_state: dict, content: str) -> str:
    parts = []
    if context_state.get("departure_area"):
        parts.append(f"从{context_state['departure_area']}出发")
    if context_state.get("activity_goal"):
        parts.append(str(context_state["activity_goal"]))
    if context_state.get("transport_hint") == "self_drive":
        parts.append("自驾")
    if context_state.get("ability_hint"):
        parts.append("中等强度" if context_state["ability_hint"].get("level") == "normal" else "有强度偏好")
    return "，".join(parts) or content[:80]


def _is_sufficient(db: Session, trip_plan: TripPlan, context_state: dict) -> bool:
    message_count = (
        db.query(TripPlanMessage)
        .filter(
            TripPlanMessage.trip_plan_id == trip_plan.id,
            TripPlanMessage.role == "user",
        )
        .count()
    )
    has_goal_and_area = bool(
        context_state.get("activity_goal") and context_state.get("departure_area")
    )
    has_complete_constraints = bool(
        context_state.get("time_window")
        and context_state.get("transport_hint")
        and context_state.get("ability_hint")
    )
    has_partial_constraints = bool(
        context_state.get("time_window")
        or context_state.get("transport_hint")
        or context_state.get("ability_hint")
    )
    return bool(
        has_goal_and_area
        and (has_complete_constraints or (message_count >= 2 and has_partial_constraints))
    )


def _run_mock_recommendation(
    db: Session,
    current_user: User,
    trip_plan: TripPlan,
    agent_run: AgentRun,
) -> tuple[str, list[TripPlanCandidateRoute], list[dict]]:
    routes = _retrieve_visible_routes(db, current_user)
    candidates: list[TripPlanCandidateRoute] = []
    for rank, (route, analysis, score) in enumerate(routes[:3], start=1):
        candidate = TripPlanCandidateRoute(
            trip_plan_id=trip_plan.id,
            agent_run_id=agent_run.id,
            route_asset_id=route.id,
            rank=rank,
            advantage_tags=_advantage_tags(route, analysis, rank),
            recommendation_reason=_recommendation_reason(route, analysis),
            score_breakdown={
                "ability_score": score,
                "preference_score": _preference_score(route),
                "evidence_score": 0.5,
            },
            planning_detail={
                "summary": f"{route.name} 是一条可作为本次出行候选的线路。",
                "risk_notes": ["近期路况未确认，出发前需要再次核实。"],
                "estimated_duration": _estimated_duration(analysis),
            },
            evidence=_mock_evidence(route),
        )
        db.add(candidate)
        candidates.append(candidate)
    db.flush()

    assistant_content = (
        "我按你的出发地、交通方式和强度偏好，先从线路库里筛了 3 条候选。"
        "天气、交通和近期路况目前是 mock 证据，出发前还需要核实。"
    )
    events = [
        _event("run.phase_changed", {"phase": "route_retrieval"}),
        _event("message.delta", {"content": assistant_content}),
        _event("message.completed", {"content": assistant_content}),
        _event(
            "candidate_routes.updated",
            {"candidate_routes": [_candidate_event(candidate) for candidate in candidates]},
        ),
        _event("run.completed", {"status": "succeeded"}),
    ]
    return assistant_content, candidates, events


def _retrieve_visible_routes(
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
        score = _ability_score(analysis, ability) + _preference_score(route)
        ranked.append((route, analysis, round(min(score, 1.0), 4)))
    ranked.sort(key=lambda item: item[2], reverse=True)
    return ranked


def _user_ability_profile(db: Session, current_user: User) -> UserAbilityProfile | None:
    return (
        db.query(UserAbilityProfile)
        .filter(UserAbilityProfile.user_id == current_user.id)
        .first()
    )


def _ability_score(
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


def _preference_score(route: RouteAsset) -> float:
    tags = set(display_tags_from_manual_tags(route.manual_tags or {}, limit=10))
    score = 0.2
    if "雪山" in tags:
        score += 0.15
    if "自驾" in tags:
        score += 0.05
    return score


def _advantage_tags(
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


def _recommendation_reason(route: RouteAsset, analysis: RouteAnalysisSnapshot) -> str:
    return (
        f"{route.name} 距离约 {analysis.distance_km:.1f} km，"
        f"累计爬升约 {analysis.elevation_gain_m:.0f} m，适合作为候选评估。"
    )


def _estimated_duration(analysis: RouteAnalysisSnapshot) -> str:
    hours = analysis.distance_km / 3.2 + analysis.elevation_gain_m / 450
    return f"约 {max(1, round(hours, 1))} 小时"


def _mock_evidence(route: RouteAsset) -> dict:
    return {
        "weather": {
            "status": "mocked",
            "summary": "天气信息为 mock，出发前需要查询真实天气。",
        },
        "transport": {
            "status": "mocked",
            "summary": "交通信息为 mock，实际耗时需要用地图确认。",
        },
        "web_evidence": {
            "status": "limited",
            "summary": "暂未接入真实 Web 搜索，不确认近期路况。",
            "sources": [],
        },
    }


def _candidate_item(db: Session, candidate: TripPlanCandidateRoute) -> CandidateRouteItem:
    route = db.get(RouteAsset, candidate.route_asset_id)
    if route is None:
        raise CandidateRouteNotFoundError
    analysis = get_latest_analysis_for_route(db, route.id)
    if analysis is None:
        raise CandidateRouteNotFoundError
    return CandidateRouteItem(
        candidate_id=candidate.id,
        rank=candidate.rank,
        route=_candidate_route_summary(route, analysis),
        advantage_tags=candidate.advantage_tags or [],
        recommendation_reason=candidate.recommendation_reason,
        score_breakdown=candidate.score_breakdown or {},
    )


def _candidate_route_summary(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
) -> CandidateRouteSummary:
    return CandidateRouteSummary(
        route_id=route.id,
        name=route.name,
        location=_route_location(route.manual_tags or {}, analysis.analysis_json or {}),
        distance_km=analysis.distance_km,
        elevation_gain_m=analysis.elevation_gain_m,
        cover_image_url=route.cover_image_url,
        display_tags=display_tags_from_manual_tags(route.manual_tags or {}),
    )


def _candidate_event(candidate: TripPlanCandidateRoute) -> dict[str, Any]:
    return {
        "candidate_id": candidate.id,
        "rank": candidate.rank,
        "advantage_tags": candidate.advantage_tags,
        "recommendation_reason": candidate.recommendation_reason,
    }


def _event(name: str, data: dict) -> dict:
    return {"event": name, "data": data}
