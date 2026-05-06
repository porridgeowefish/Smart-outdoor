from __future__ import annotations

import json
from typing import Any

from app.features.trip_plans.model import TripPlanCandidateRoute


def event(name: str, data: dict) -> dict:
    return {"event": name, "data": data}


def candidate_event(candidate: TripPlanCandidateRoute) -> dict[str, Any]:
    return {
        "candidate_id": candidate.id,
        "rank": candidate.rank,
        "advantage_tags": candidate.advantage_tags,
        "recommendation_reason": candidate.recommendation_reason,
    }


def sse_lines(events: list[dict]) -> str:
    chunks = []
    for item in events:
        chunks.append(f"event: {item['event']}\n")
        chunks.append(f"data: {json.dumps(item['data'], ensure_ascii=False)}\n\n")
    return "".join(chunks)
