from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TripPlanMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=2000)
    trip_plan_id: str | None = None


class TripPlanMessageResponse(BaseModel):
    id: str
    role: str
    content: str


class CandidateRouteSummary(BaseModel):
    route_id: str
    name: str
    location: str
    distance_km: float
    elevation_gain_m: float
    cover_image_url: str | None
    display_tags: list[str]


class CandidateRouteItem(BaseModel):
    candidate_id: str
    rank: int
    route: CandidateRouteSummary
    advantage_tags: list[str]
    recommendation_reason: str
    score_breakdown: dict


class TripPlanMessagePostResponse(BaseModel):
    trip_plan_id: str
    user_message_id: str
    assistant_message: TripPlanMessageResponse
    agent_run_id: str
    run_status: str
    candidate_routes: list[CandidateRouteItem]


class CandidateRouteDetailResponse(BaseModel):
    candidate_id: str
    rank: int
    route: CandidateRouteSummary
    advantage_tags: list[str]
    recommendation_reason: str
    score_breakdown: dict
    planning_detail: dict
    evidence: dict
