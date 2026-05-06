from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.trip_plans.schemas import (
    CandidateRouteDetailResponse,
    TripPlanMessagePostResponse,
    TripPlanMessageRequest,
)
from app.features.trip_plans.service import (
    AgentRunNotFoundError,
    CandidateRouteNotFoundError,
    TripPlanClosedError,
    TripPlanNotFoundError,
    get_agent_run_events,
    get_candidate_detail,
    handle_user_message,
    sse_lines,
)
from app.features.users.deps import get_current_user
from app.features.users.model import User

router = APIRouter(tags=["trip-plans"])


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
