from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TripPlan(Base):
    __tablename__ = "trip_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )


class TripPlanMessage(Base):
    __tablename__ = "trip_plan_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plans.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(32), default="text")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plans.id"), index=True
    )
    user_message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plan_messages.id"), index=True
    )
    run_status: Mapped[str] = mapped_column(String(32), default="running")
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )


class TripPlanCandidateRoute(Base):
    __tablename__ = "trip_plan_candidate_routes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plans.id"), index=True
    )
    agent_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_runs.id"), index=True
    )
    route_asset_id: Mapped[str] = mapped_column(String(36), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    advantage_tags: Mapped[list] = mapped_column(JSON, default=list)
    recommendation_reason: Mapped[str] = mapped_column(Text)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    planning_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class RoutePlanSnapshot(Base):
    __tablename__ = "route_plan_snapshots"
    __table_args__ = (UniqueConstraint("source_candidate_id", name="uq_route_plan_snapshot_candidate"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    continue_trip_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plans.id"), index=True
    )
    source_candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trip_plan_candidate_routes.id"), index=True
    )
    route_asset_id: Mapped[str] = mapped_column(String(36), index=True)
    route_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    recommendation_reason: Mapped[str] = mapped_column(Text)
    advantage_tags: Mapped[list] = mapped_column(JSON, default=list)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    planning_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
