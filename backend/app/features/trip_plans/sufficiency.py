from __future__ import annotations

from sqlalchemy.orm import Session

from app.features.trip_plans.model import TripPlan, TripPlanMessage


def is_sufficient(db: Session, trip_plan: TripPlan, context_state: dict) -> bool:
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
