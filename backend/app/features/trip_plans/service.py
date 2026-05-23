from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.features.llm.provider import get_llm_provider
from app.features.llm.schemas import ContextExtractionInput
from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.router import _route_cover_url, _route_location
from app.features.routes.service import (
    build_track_preview,
    display_tags_from_manual_tags,
    get_latest_analysis_for_route,
)
from app.features.trip_plans.events import event, sse_lines
from app.features.trip_plans.context import (
    confirmed_context,
    context_summary,
    merge_choice_answers,
    merge_text_context_state,
    missing_context_fields,
)
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
    ChoiceRequest,
    ChoiceResultRequest,
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


class ChoiceRequestNotFoundError(Exception):
    pass


class ChoiceRequestNotActiveError(Exception):
    pass


class InvalidChoiceResultError(Exception):
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
    existing_context_state = trip_plan.context_state or {}
    context_result = llm_provider.extract_context(
        ContextExtractionInput(
            existing_context_state=existing_context_state,
            content=content,
        )
    )
    merged_context = merge_text_context_state(
        existing_context_state,
        context_result.context_state,
        content,
    )
    trip_plan.context_state = merged_context
    trip_plan.context_summary = context_summary(merged_context, content)
    db.add(trip_plan)

    if is_sufficient(db, trip_plan, merged_context):
        assistant_content, candidates, events = run_mock_recommendation(
            db, current_user, trip_plan, agent_run, llm_provider
        )
        agent_run.run_status = "succeeded"
        choice_request = None
        assistant_content_type = "text"
        assistant_payload = None
    else:
        candidates = []
        choice_request = _build_choice_request(merged_context)
        assistant_content = _choice_request_content(choice_request)
        assistant_content_type = "choice_request"
        assistant_payload = _choice_request_payload(choice_request)
        events = [
            event("run.phase_changed", {"phase": "sufficiency_check"}),
            event("message.delta", {"content": assistant_content}),
            event("message.completed", {"content": assistant_content}),
            event("run.waiting_user", {"missing_fields": missing_context_fields(merged_context)}),
            event("run.completed", {"status": "waiting_user"}),
        ]
        agent_run.run_status = "waiting_user"

    assistant_message = TripPlanMessage(
        trip_plan_id=trip_plan.id,
        role="assistant",
        content=assistant_content,
        content_type=assistant_content_type,
        payload=assistant_payload,
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
            content_type=assistant_message.content_type,
            payload=assistant_message.payload,
            created_at=assistant_message.created_at.isoformat(),
        ),
        agent_run_id=agent_run.id,
        run_status=agent_run.run_status,
        choice_request=choice_request,
        confirmed_context=confirmed_context(trip_plan.context_state or {}),
        missing_fields=missing_context_fields(trip_plan.context_state or {}),
        candidate_routes=[_candidate_item(db, candidate) for candidate in candidates],
    )


def handle_choice_results(
    db: Session,
    current_user: User,
    *,
    trip_plan_id: str,
    payload: ChoiceResultRequest,
) -> TripPlanMessagePostResponse:
    trip_plan = db.get(TripPlan, trip_plan_id)
    if trip_plan is None or trip_plan.user_id != current_user.id:
        raise TripPlanNotFoundError
    if trip_plan.status == "closed":
        raise TripPlanClosedError
    choice_request_message = _find_choice_request_message(
        db,
        trip_plan_id=trip_plan_id,
        choice_request_id=payload.choice_request_id,
    )
    _ensure_choice_request_active(db, trip_plan_id, payload.choice_request_id)
    _validate_choice_answers(choice_request_message.payload or {}, payload)

    try:
        merged_context = merge_choice_answers(trip_plan.context_state or {}, payload.answers)
    except ValueError as exc:
        raise InvalidChoiceResultError(str(exc)) from exc
    trip_plan.context_state = merged_context
    trip_plan.context_summary = context_summary(merged_context, _choice_result_content(payload))
    db.add(trip_plan)

    user_message = TripPlanMessage(
        trip_plan_id=trip_plan.id,
        role="user",
        content=_choice_result_content(payload),
        content_type="choice_result",
        payload={
            "choice_request_id": payload.choice_request_id,
            "answers": [answer.model_dump() for answer in payload.answers],
        },
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
    if is_sufficient(db, trip_plan, merged_context):
        assistant_content, candidates, events = run_mock_recommendation(
            db, current_user, trip_plan, agent_run, llm_provider
        )
        agent_run.run_status = "succeeded"
        choice_request = None
        assistant_content_type = "text"
        assistant_payload = None
    else:
        candidates = []
        choice_request = _build_choice_request(merged_context)
        assistant_content = _choice_request_content(choice_request)
        assistant_content_type = "choice_request"
        assistant_payload = _choice_request_payload(choice_request)
        events = [
            event("run.phase_changed", {"phase": "sufficiency_check"}),
            event("message.delta", {"content": assistant_content}),
            event("message.completed", {"content": assistant_content}),
            event("run.waiting_user", {"missing_fields": missing_context_fields(merged_context)}),
            event("run.completed", {"status": "waiting_user"}),
        ]
        agent_run.run_status = "waiting_user"

    assistant_message = TripPlanMessage(
        trip_plan_id=trip_plan.id,
        role="assistant",
        content=assistant_content,
        content_type=assistant_content_type,
        payload=assistant_payload,
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
            content_type=assistant_message.content_type,
            payload=assistant_message.payload,
            created_at=assistant_message.created_at.isoformat(),
        ),
        agent_run_id=agent_run.id,
        run_status=agent_run.run_status,
        choice_request=choice_request,
        confirmed_context=confirmed_context(trip_plan.context_state or {}),
        missing_fields=missing_context_fields(trip_plan.context_state or {}),
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
                content_type=message.content_type,
                payload=message.payload,
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


def _build_choice_request(context_state: dict) -> ChoiceRequest:
    questions = [
        _question_for_field(field)
        for field in missing_context_fields(context_state or {})[:3]
    ]
    return ChoiceRequest(
        choice_request_id=f"choice_req_{uuid.uuid4()}",
        questions=questions,
    )


def _question_for_field(field: str) -> dict[str, Any]:
    if field == "departure_area":
        return {
            "type": "text",
            "field": field,
            "question": "这次从哪里出发？",
            "header": "出发地",
            "options": [],
            "multi_select": False,
            "allow_custom": True,
        }
    if field == "activity_goal":
        return {
            "type": "text",
            "field": field,
            "question": "这次想怎么走，或者主要想看什么？",
            "header": "目标",
            "options": [],
            "multi_select": False,
            "allow_custom": True,
        }
    if field == "time_window":
        return {
            "type": "text",
            "field": field,
            "question": "大概什么时候出发、计划几天？",
            "header": "时间",
            "options": [],
            "multi_select": False,
            "allow_custom": True,
        }
    if field == "terrain_tolerance":
        return {
            "type": "single_choice",
            "field": field,
            "question": "如果涉及冰雪或野路，你能接受到什么程度？",
            "header": "路况",
            "options": [
                {
                    "label": "尽量避开冰雪路",
                    "value": "avoid_icy_road",
                    "description": "优先看远处雪景或更稳妥的路面。",
                },
                {
                    "label": "接受常规山路",
                    "value": "accept_normal_trail",
                    "description": "可以接受普通山路，但不主动选择高风险路段。",
                },
            ],
            "multi_select": False,
            "allow_custom": True,
        }
    return {
        "type": "single_choice",
        "field": "transport_hint",
        "question": "这次交通方式你更倾向哪种？",
        "header": "交通",
        "options": [
            {
                "label": "自驾",
                "value": "self_drive",
                "description": "路线选择更灵活，但需要考虑停车和返程。",
            },
            {
                "label": "公共交通",
                "value": "public_transport",
                "description": "优先匹配公交或接驳更方便的路线。",
            },
            {
                "label": "都可以，帮我权衡",
                "value": "flexible",
                "description": "系统可以同时比较自驾和公共交通。",
            },
        ],
        "multi_select": False,
        "allow_custom": True,
    }


def _choice_request_payload(choice_request: ChoiceRequest) -> dict:
    return {
        "tool_name": "ask_user_choice",
        "input": choice_request.model_dump(),
    }


def _choice_request_content(choice_request: ChoiceRequest) -> str:
    headers = "、".join(question.header for question in choice_request.questions)
    if "交通" in headers:
        headers = headers.replace("交通", "交通方式")
    return f"我先确认{headers}，这样推荐会更稳。"


def _choice_result_content(payload: ChoiceResultRequest) -> str:
    labels = []
    for answer in payload.answers:
        label = answer.custom_text or answer.label
        labels.append("、".join(label) if isinstance(label, list) else str(label))
    return f"选择：{'；'.join(labels)}"


def _find_choice_request_message(
    db: Session,
    *,
    trip_plan_id: str,
    choice_request_id: str,
) -> TripPlanMessage:
    messages = (
        db.query(TripPlanMessage)
        .filter(
            TripPlanMessage.trip_plan_id == trip_plan_id,
            TripPlanMessage.content_type == "choice_request",
        )
        .order_by(TripPlanMessage.created_at.desc())
        .all()
    )
    for message in messages:
        payload = message.payload or {}
        input_payload = payload.get("input") or {}
        if input_payload.get("choice_request_id") == choice_request_id:
            return message
    raise ChoiceRequestNotFoundError


def _ensure_choice_request_active(
    db: Session,
    trip_plan_id: str,
    choice_request_id: str,
) -> None:
    active_choice_request_id: str | None = None
    messages = (
        db.query(TripPlanMessage)
        .filter(TripPlanMessage.trip_plan_id == trip_plan_id)
        .order_by(TripPlanMessage.created_at.asc())
        .all()
    )
    for message in messages:
        if message.content_type == "choice_request":
            active_choice_request_id = _choice_request_id_from_message(message)
        elif message.content_type == "choice_result":
            result_choice_request_id = (message.payload or {}).get("choice_request_id")
            if result_choice_request_id == active_choice_request_id:
                active_choice_request_id = None
    if active_choice_request_id != choice_request_id:
        raise ChoiceRequestNotActiveError


def _choice_request_id_from_message(message: TripPlanMessage) -> str | None:
    payload = message.payload or {}
    input_payload = payload.get("input") or {}
    value = input_payload.get("choice_request_id")
    return str(value) if value else None


def _validate_choice_answers(request_payload: dict, payload: ChoiceResultRequest) -> None:
    input_payload = request_payload.get("input") or {}
    questions = {
        question.get("field"): question for question in input_payload.get("questions") or []
    }
    answer_fields = {answer.field for answer in payload.answers}
    if answer_fields != set(questions):
        raise InvalidChoiceResultError
    for answer in payload.answers:
        question = questions.get(answer.field)
        if question is None:
            raise InvalidChoiceResultError
        if question.get("type") == "text":
            continue
        if question.get("multi_select") and not isinstance(answer.value, list):
            raise InvalidChoiceResultError
        if not question.get("multi_select") and isinstance(answer.value, list):
            raise InvalidChoiceResultError
        option_values = {
            option.get("value") for option in question.get("options") or []
        }
        values = answer.value if isinstance(answer.value, list) else [answer.value]
        unknown_values = [value for value in values if value not in option_values]
        if unknown_values and not question.get("allow_custom"):
            raise InvalidChoiceResultError


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
        cover_image_url=_route_cover_url(route, preferred="thumbnail"),
        display_tags=display_tags_from_manual_tags(route.manual_tags or {}),
        track_preview=build_track_preview(analysis),
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
