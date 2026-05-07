from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.trip_plans.schemas import (
    CandidateRouteDetailResponse,
    RoutePlanSnapshotDetailResponse,
    RoutePlanSnapshotListResponse,
    TripPlanConversationResponse,
    TripPlanListResponse,
    TripPlanMessagePostResponse,
    TripPlanMessageRequest,
)
from app.features.trip_plans.service import (
    AgentRunNotFoundError,
    CandidateRouteNotFoundError,
    RoutePlanSnapshotExistsError,
    RoutePlanSnapshotNotFoundError,
    TripPlanClosedError,
    TripPlanNotFoundError,
    get_agent_run_events,
    get_candidate_detail,
    get_route_plan_snapshot_detail,
    get_trip_plan_conversation,
    handle_user_message,
    list_trip_plans,
    list_route_plan_snapshots,
    save_candidate_route_snapshot,
    sse_lines,
)
from app.features.users.deps import get_current_user
from app.features.users.model import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["trip-plans"])


@router.get("/trip-plans", response_model=TripPlanListResponse)
def read_trip_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_trip_plans(db, current_user)


@router.get("/trip-plans/{trip_plan_id}/messages", response_model=TripPlanConversationResponse)
def read_trip_plan_messages(
    trip_plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_trip_plan_conversation(db, current_user, trip_plan_id)
    except TripPlanNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "code": "TRIP_PLAN_NOT_FOUND",
                "message": "Trip plan not found",
            },
        )


@router.post("/trip-plans/messages", response_model=TripPlanMessagePostResponse)
def post_trip_plan_message(
    payload: TripPlanMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return handle_user_message(
            db,
            current_user,
            content=payload.content,
            trip_plan_id=payload.trip_plan_id,
        )
    except TripPlanClosedError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "TRIP_PLAN_CLOSED",
                "message": "Trip plan is closed",
            },
        )
    except TripPlanNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "code": "TRIP_PLAN_NOT_FOUND",
                "message": "Trip plan not found",
            },
        )
    except Exception as exc:
        logger.exception("Agent workflow failed")
        return JSONResponse(
            status_code=500,
            content={
                "code": "AGENT_ERROR",
                "message": f"Agent 处理失败：{exc}",
            },
        )


@router.get("/agent-runs/{agent_run_id}/events")
def read_agent_run_events(
    agent_run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        events = get_agent_run_events(db, current_user, agent_run_id)
    except AgentRunNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"code": "AGENT_RUN_NOT_FOUND", "message": "Agent run not found"},
        )
    return Response(content=sse_lines(events), media_type="text/event-stream")


@router.get(
    "/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}",
    response_model=CandidateRouteDetailResponse,
)
def read_candidate_route_detail(
    trip_plan_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_candidate_detail(db, current_user, trip_plan_id, candidate_id)
    except CandidateRouteNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "code": "CANDIDATE_ROUTE_NOT_FOUND",
                "message": "Candidate route not found",
            },
        )


@router.post(
    "/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save",
    response_model=RoutePlanSnapshotDetailResponse,
    status_code=201,
)
def save_candidate_route(
    trip_plan_id: str,
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return save_candidate_route_snapshot(db, current_user, trip_plan_id, candidate_id)
    except CandidateRouteNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "code": "CANDIDATE_ROUTE_NOT_FOUND",
                "message": "Candidate route not found",
            },
        )
    except RoutePlanSnapshotExistsError:
        return JSONResponse(
            status_code=409,
            content={
                "code": "ROUTE_PLAN_SNAPSHOT_EXISTS",
                "message": "该候选规划已经保存",
            },
        )


@router.get(
    "/my/route-plan-snapshots",
    response_model=RoutePlanSnapshotListResponse,
)
def read_my_route_plan_snapshots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_route_plan_snapshots(db, current_user)


@router.get(
    "/my/route-plan-snapshots/{snapshot_id}",
    response_model=RoutePlanSnapshotDetailResponse,
)
def read_my_route_plan_snapshot_detail(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_route_plan_snapshot_detail(db, current_user, snapshot_id)
    except RoutePlanSnapshotNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "code": "ROUTE_PLAN_SNAPSHOT_NOT_FOUND",
                "message": "Route plan snapshot not found",
            },
        )
