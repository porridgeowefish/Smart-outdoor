from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TripPlanMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=2000)
    trip_plan_id: str | None = None


class TripPlanMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    content_type: Literal["text", "choice_request", "choice_result"] = "text"
    payload: dict[str, Any] | None = None
    created_at: str | None = None


class ChoiceOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    description: str | None = None


class ChoiceQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["single_choice", "multi_choice", "text"]
    field: str
    question: str
    header: str
    options: list[ChoiceOption] = Field(default_factory=list)
    multi_select: bool = False
    allow_custom: bool = True


class ChoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choice_request_id: str
    questions: list[ChoiceQuestion] = Field(min_length=1, max_length=3)


class ChoiceAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    value: str | list[str]
    label: str | list[str]
    custom_text: str | None = None


class ChoiceResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choice_request_id: str
    answers: list[ChoiceAnswer] = Field(min_length=1)


class ConfirmedContextItem(BaseModel):
    field: str
    label: str
    value: str


class ConfirmedContext(BaseModel):
    items: list[ConfirmedContextItem] = Field(default_factory=list)


class CandidateRouteSummary(BaseModel):
    route_id: str
    name: str
    location: str
    distance_km: float
    elevation_gain_m: float
    cover_image_url: str | None
    display_tags: list[str]
    track_preview: dict | None = None


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
    choice_request: ChoiceRequest | None = None
    confirmed_context: ConfirmedContext = Field(default_factory=ConfirmedContext)
    missing_fields: list[str] = Field(default_factory=list)
    candidate_routes: list[CandidateRouteItem]


class TripPlanListItem(BaseModel):
    trip_plan_id: str
    title: str
    status: str
    context_summary: str | None
    updated_at: str


class TripPlanListResponse(BaseModel):
    items: list[TripPlanListItem]
    total: int


class TripPlanConversationResponse(BaseModel):
    trip_plan_id: str
    title: str
    status: str
    context_summary: str | None
    messages: list[TripPlanMessageResponse]
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


class RoutePlanSnapshotItem(BaseModel):
    snapshot_id: str
    continue_trip_plan_id: str
    source_candidate_id: str
    route: CandidateRouteSummary
    advantage_tags: list[str]
    recommendation_reason: str
    created_at: str


class RoutePlanSnapshotListResponse(BaseModel):
    items: list[RoutePlanSnapshotItem]
    total: int


class RoutePlanSnapshotDetailResponse(BaseModel):
    snapshot_id: str
    continue_trip_plan_id: str
    source_candidate_id: str
    route: CandidateRouteSummary
    advantage_tags: list[str]
    recommendation_reason: str
    score_breakdown: dict
    planning_detail: dict
    evidence: dict
    created_at: str
