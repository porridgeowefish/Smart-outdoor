from __future__ import annotations

from sqlalchemy.orm import Session

from app.features.trip_plans.context import missing_context_fields
from app.features.trip_plans.model import TripPlan


def is_sufficient(db: Session, trip_plan: TripPlan, context_state: dict) -> bool:
    return not missing_context_fields(context_state or {})
