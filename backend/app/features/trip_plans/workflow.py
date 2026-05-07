from __future__ import annotations

from sqlalchemy.orm import Session

from app.features.llm.provider import AgentLLMProvider
from app.features.llm.schemas import ResponseGenerationInput
from app.features.trip_plans.evaluation import (
    advantage_tags,
    planning_detail,
    recommendation_reason,
    score_breakdown,
)
from app.features.trip_plans.evaluator import evaluate_candidate_output
from app.features.trip_plans.evidence import candidate_evidence
from app.features.trip_plans.events import candidate_event, event
from app.features.trip_plans.model import AgentRun, TripPlan, TripPlanCandidateRoute
from app.features.trip_plans.retrieval import retrieve_visible_routes
from app.features.users.model import User


def run_mock_recommendation(
    db: Session,
    current_user: User,
    trip_plan: TripPlan,
    agent_run: AgentRun,
    llm_provider: AgentLLMProvider,
) -> tuple[str, list[TripPlanCandidateRoute], list[dict]]:
    routes = retrieve_visible_routes(db, current_user, trip_plan.context_state or {})
    candidates: list[TripPlanCandidateRoute] = []
    for rank, (route, analysis, score) in enumerate(routes[:3], start=1):
        detail = planning_detail(route, analysis)
        detail["matched_tags"] = score.matched_tags
        detail["route_tags"] = score.route_tags[:12]
        evidence = candidate_evidence(route, analysis, trip_plan.context_state or {})
        evidence["evaluator"] = evaluate_candidate_output(detail, evidence)
        detail["llm_detail_card"] = llm_provider.generate_response(
            ResponseGenerationInput(
                kind="candidate_detail_card",
                context_state=trip_plan.context_state or {},
                candidate_count=1,
                candidate_routes=[
                    {
                        "rank": rank,
                        "route_name": route.name,
                        "distance_km": analysis.distance_km,
                        "elevation_gain_m": analysis.elevation_gain_m,
                        "matched_tags": score.matched_tags,
                        "planning_detail": detail,
                        "evidence": evidence,
                    }
                ],
            )
        ).content
        candidate = TripPlanCandidateRoute(
            trip_plan_id=trip_plan.id,
            agent_run_id=agent_run.id,
            route_asset_id=route.id,
            rank=rank,
            advantage_tags=advantage_tags(route, analysis, rank),
            recommendation_reason=recommendation_reason(route, analysis),
            score_breakdown=score_breakdown(route, score),
            planning_detail=detail,
            evidence=evidence,
        )
        db.add(candidate)
        candidates.append(candidate)
    db.flush()

    assistant_content = llm_provider.generate_response(
        ResponseGenerationInput(
            kind="recommendation",
            context_state=trip_plan.context_state or {},
            candidate_count=len(candidates),
            candidate_routes=[
                {
                    "rank": candidate.rank,
                    "route_name": route.name,
                    "distance_km": analysis.distance_km,
                    "elevation_gain_m": analysis.elevation_gain_m,
                    "advantage_tags": candidate.advantage_tags or [],
                    "recommendation_reason": candidate.recommendation_reason,
                    "score_breakdown": score_breakdown(route, _score),
                    "evidence_status": {
                        "weather": (candidate.evidence or {}).get("weather", {}).get("status"),
                        "transport": (candidate.evidence or {}).get("transport", {}).get("status"),
                        "web_evidence": (candidate.evidence or {})
                        .get("web_evidence", {})
                        .get("status"),
                    },
                }
                for candidate, (route, analysis, _score) in zip(candidates, routes[:3])
            ],
        )
    ).content
    events = [
        event("run.phase_changed", {"phase": "route_retrieval"}),
        event("message.delta", {"content": assistant_content}),
        event("message.completed", {"content": assistant_content}),
        event(
            "candidate_routes.updated",
            {"candidate_routes": [candidate_event(candidate) for candidate in candidates]},
        ),
        event("run.completed", {"status": "succeeded"}),
    ]
    return assistant_content, candidates, events
