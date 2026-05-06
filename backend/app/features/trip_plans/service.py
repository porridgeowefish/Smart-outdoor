from __future__ import annotations

from sqlalchemy.orm import Session

from app.features.llm.provider import get_llm_provider
from app.features.llm.schemas import ContextExtractionInput, ResponseGenerationInput
from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.router import _route_location
from app.features.routes.service import display_tags_from_manual_tags, get_latest_analysis_for_route
from app.features.trip_plans.events import event, sse_lines
from app.features.trip_plans.model import (
    AgentRun,
    RoutePlanSnapshot,
    TripPlan,
    TripPlanCandidateRoute,
    TripPlanMessage,
)
from app.features.trip_plans.schemas import (
    CandidateRouteDetailResponse,
    CandidateRouteItem,
    CandidateRouteSummary,
    RoutePlanSnapshotDetailResponse,
    RoutePlanSnapshotItem,
    RoutePlanSnapshotListResponse,
    TripPlanConversationResponse,
    TripPlanListItem,
    TripPlanListResponse,
    TripPlanMessagePostResponse,
    TripPlanMessageResponse,
)
from app.features.trip_plans.sufficiency import is_sufficient
from app.features.trip_plans.workflow import run_mock_recommendation
from app.features.users.model import User


class TripPlanNotFoundError(Exception):
    pass


class TripPlanClosedError(Exception):
    pass


class AgentRunNotFoundError(Exception):
    pass


class CandidateRouteNotFoundError(Exception):
    pass


class RoutePlanSnapshotNotFoundError(Exception):
    pass


class RoutePlanSnapshotExistsError(Exception):
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

    llm_provider = get_llm_provider()
    context_result = llm_provider.extract_context(
        ContextExtractionInput(
            existing_context_state=trip_plan.context_state or {},
            content=content,
        )
    )
    trip_plan.context_state = context_result.context_state
    trip_plan.context_summary = context_result.context_summary
    db.add(trip_plan)

    if is_sufficient(db, trip_plan, context_result.context_state):
        assistant_content, candidates, events = run_mock_recommendation(
            db, current_user, trip_plan, agent_run, llm_provider
        )
        agent_run.run_status = "succeeded"
    else:
        candidates = []
        assistant_content = llm_provider.generate_response(
            ResponseGenerationInput(
                kind="waiting_user",
                context_state=context_result.context_state,
            )
        ).content
        events = [
            event("run.phase_changed", {"phase": "sufficiency_check"}),
            event("message.delta", {"content": assistant_content}),
            event("message.completed", {"content": assistant_content}),
            event("run.waiting_user", {"missing_fields": ["transport_hint", "ability_hint"]}),
            event("run.completed", {"status": "waiting_user"}),
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
            created_at=assistant_message.created_at.isoformat(),
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


def list_trip_plans(db: Session, current_user: User) -> TripPlanListResponse:
    trip_plans = (
        db.query(TripPlan)
        .filter(TripPlan.user_id == current_user.id)
        .order_by(TripPlan.updated_at.desc())
        .all()
    )
    return TripPlanListResponse(
        items=[_trip_plan_item(trip_plan) for trip_plan in trip_plans],
        total=len(trip_plans),
    )


def get_trip_plan_conversation(
    db: Session,
    current_user: User,
    trip_plan_id: str,
) -> TripPlanConversationResponse:
    trip_plan = db.get(TripPlan, trip_plan_id)
    if trip_plan is None or trip_plan.user_id != current_user.id:
        raise TripPlanNotFoundError
    messages = (
        db.query(TripPlanMessage)
        .filter(TripPlanMessage.trip_plan_id == trip_plan_id)
        .order_by(TripPlanMessage.created_at.asc())
        .all()
    )
    latest_agent_run = (
        db.query(AgentRun)
        .filter(AgentRun.trip_plan_id == trip_plan_id)
        .order_by(AgentRun.created_at.desc())
        .first()
    )
    candidates: list[TripPlanCandidateRoute] = []
    if latest_agent_run is not None:
        candidates = (
            db.query(TripPlanCandidateRoute)
            .filter(TripPlanCandidateRoute.agent_run_id == latest_agent_run.id)
            .order_by(TripPlanCandidateRoute.rank.asc())
            .all()
        )
    return TripPlanConversationResponse(
        trip_plan_id=trip_plan.id,
        title=trip_plan.title,
        status=trip_plan.status,
        context_summary=trip_plan.context_summary,
        messages=[
            TripPlanMessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
            )
            for message in messages
        ],
        candidate_routes=[_candidate_item(db, candidate) for candidate in candidates],
    )


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


def save_candidate_route_snapshot(
    db: Session,
    current_user: User,
    trip_plan_id: str,
    candidate_id: str,
) -> RoutePlanSnapshotDetailResponse:
    trip_plan = db.get(TripPlan, trip_plan_id)
    if trip_plan is None or trip_plan.user_id != current_user.id:
        raise CandidateRouteNotFoundError
    candidate = db.get(TripPlanCandidateRoute, candidate_id)
    if candidate is None or candidate.trip_plan_id != trip_plan_id:
        raise CandidateRouteNotFoundError

    existing = (
        db.query(RoutePlanSnapshot)
        .filter(RoutePlanSnapshot.source_candidate_id == candidate_id)
        .first()
    )
    if existing is not None:
        raise RoutePlanSnapshotExistsError

    candidate_item = _candidate_item(db, candidate)
    snapshot = RoutePlanSnapshot(
        user_id=current_user.id,
        continue_trip_plan_id=trip_plan_id,
        source_candidate_id=candidate_id,
        route_asset_id=candidate.route_asset_id,
        route_summary=candidate_item.route.model_dump(),
        recommendation_reason=candidate.recommendation_reason,
        advantage_tags=candidate.advantage_tags or [],
        score_breakdown=candidate.score_breakdown or {},
        planning_detail=candidate.planning_detail or {},
        evidence=candidate.evidence or {},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return _snapshot_detail(snapshot)


def list_route_plan_snapshots(
    db: Session,
    current_user: User,
) -> RoutePlanSnapshotListResponse:
    snapshots = (
        db.query(RoutePlanSnapshot)
        .filter(RoutePlanSnapshot.user_id == current_user.id)
        .order_by(RoutePlanSnapshot.created_at.desc())
        .all()
    )
    return RoutePlanSnapshotListResponse(
        items=[_snapshot_item(snapshot) for snapshot in snapshots],
        total=len(snapshots),
    )


def get_route_plan_snapshot_detail(
    db: Session,
    current_user: User,
    snapshot_id: str,
) -> RoutePlanSnapshotDetailResponse:
    snapshot = db.get(RoutePlanSnapshot, snapshot_id)
    if snapshot is None or snapshot.user_id != current_user.id:
        raise RoutePlanSnapshotNotFoundError
    return _snapshot_detail(snapshot)


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

    trip_plan = TripPlan(
        user_id=current_user.id,
        title=content.strip()[:40] or "新的出行规划",
        status="draft",
        context_summary="",
        context_state={},
    )
    db.add(trip_plan)
    db.flush()
    return trip_plan


def _trip_plan_item(trip_plan: TripPlan) -> TripPlanListItem:
    return TripPlanListItem(
        trip_plan_id=trip_plan.id,
        title=trip_plan.title,
        status=trip_plan.status,
        context_summary=trip_plan.context_summary,
        updated_at=trip_plan.updated_at.isoformat(),
    )


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


def _snapshot_item(snapshot: RoutePlanSnapshot) -> RoutePlanSnapshotItem:
    return RoutePlanSnapshotItem(
        snapshot_id=snapshot.id,
        continue_trip_plan_id=snapshot.continue_trip_plan_id,
        source_candidate_id=snapshot.source_candidate_id,
        route=CandidateRouteSummary.model_validate(snapshot.route_summary),
        advantage_tags=snapshot.advantage_tags or [],
        recommendation_reason=snapshot.recommendation_reason,
        created_at=snapshot.created_at.isoformat(),
    )


def _snapshot_detail(snapshot: RoutePlanSnapshot) -> RoutePlanSnapshotDetailResponse:
    return RoutePlanSnapshotDetailResponse(
        snapshot_id=snapshot.id,
        continue_trip_plan_id=snapshot.continue_trip_plan_id,
        source_candidate_id=snapshot.source_candidate_id,
        route=CandidateRouteSummary.model_validate(snapshot.route_summary),
        advantage_tags=snapshot.advantage_tags or [],
        recommendation_reason=snapshot.recommendation_reason,
        score_breakdown=snapshot.score_breakdown or {},
        planning_detail=snapshot.planning_detail or {},
        evidence=snapshot.evidence or {},
        created_at=snapshot.created_at.isoformat(),
    )
