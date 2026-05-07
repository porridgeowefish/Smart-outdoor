from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.routes.test_route_upload_api import VALID_GPX


def _register_and_login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "plain_password",
            "nickname": username,
        },
    )
    assert response.status_code == 201
    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "plain_password"},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def _upload_public_route(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    manual_tags: dict | None = None,
) -> str:
    response = client.post(
        "/api/routes/upload",
        headers=headers,
        data={
            "name": name,
            "description": f"{name} description",
            "visibility": "public",
            "manual_tags": json.dumps(manual_tags or {}),
        },
        files={"file": (f"{name}.gpx", VALID_GPX, "application/gpx+xml")},
    )
    assert response.status_code == 200
    assert response.json()["parse_status"] == "parsed"
    return response.json()["route_id"]


def test_send_first_message_creates_trip_plan_and_agent_run(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "周末想从成都出发看雪山"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trip_plan_id"]
    assert body["user_message_id"]
    assert body["agent_run_id"]
    assert body["run_status"] == "waiting_user"
    assert body["assistant_message"]["role"] == "assistant"
    assert "交通方式" in body["assistant_message"]["content"]


def test_send_followup_message_appends_to_existing_trip_plan_and_returns_candidates(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for name, tags in [
        ("Snow mountain route", {"scenery": ["雪山"], "transport": ["自驾"]}),
        ("Forest route", {"scenery": ["森林"], "transport": ["自驾"]}),
        ("Family route", {"scenery": ["亲子"], "transport": ["自驾"]}),
    ]:
        _upload_public_route(client, auth_headers, name=name, manual_tags=tags)

    first_response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "周末想从成都出发看雪山"},
    )
    trip_plan_id = first_response.json()["trip_plan_id"]

    second_response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={
            "trip_plan_id": trip_plan_id,
            "content": "自驾，一天往返，中等强度",
        },
    )

    assert second_response.status_code == 200
    body = second_response.json()
    assert body["trip_plan_id"] == trip_plan_id
    assert body["run_status"] == "succeeded"
    assert len(body["candidate_routes"]) == 3
    assert body["candidate_routes"][0]["rank"] == 1
    assert body["candidate_routes"][0]["route"]["route_id"]
    assert body["candidate_routes"][0]["route"]["track_preview"]["format"] == "geojson"
    assert body["candidate_routes"][0]["recommendation_reason"]


def test_agent_run_events_returns_sse_contract(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for index in range(3):
        _upload_public_route(client, auth_headers, name=f"Route {index}")

    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "成都周边自驾一日徒步，中等强度"},
    )
    agent_run_id = response.json()["agent_run_id"]

    events_response = client.get(
        f"/api/agent-runs/{agent_run_id}/events",
        headers=auth_headers,
    )

    assert events_response.status_code == 200
    body = events_response.text
    assert "event: run.phase_changed" in body
    assert "event: message.delta" in body
    assert "event: message.completed" in body
    assert "event: candidate_routes.updated" in body
    assert "event: run.completed" in body


def test_list_trip_plans_and_load_conversation(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _upload_public_route(client, auth_headers, name="History route")
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "成都周边自驾一日徒步，中等强度"},
    )
    trip_plan_id = response.json()["trip_plan_id"]

    list_response = client.get("/api/trip-plans", headers=auth_headers)
    detail_response = client.get(
        f"/api/trip-plans/{trip_plan_id}/messages",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1
    assert list_response.json()["items"][0]["trip_plan_id"] == trip_plan_id
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["trip_plan_id"] == trip_plan_id
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]
    assert detail["candidate_routes"]


def test_user_cannot_load_other_users_trip_plan_conversation(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "trip_history_other")
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "周末想从成都出发看雪山"},
    )

    detail_response = client.get(
        f"/api/trip-plans/{response.json()['trip_plan_id']}/messages",
        headers=other_headers,
    )

    assert detail_response.status_code == 404
    assert detail_response.json()["code"] == "TRIP_PLAN_NOT_FOUND"


def test_candidate_detail_returns_route_planning_detail_and_evidence(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _upload_public_route(client, auth_headers, name="Candidate route")
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "成都周边自驾一日徒步，中等强度"},
    )
    candidate = response.json()["candidate_routes"][0]

    detail_response = client.get(
        f"/api/trip-plans/{response.json()['trip_plan_id']}/candidate-routes/{candidate['candidate_id']}",
        headers=auth_headers,
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["candidate_id"] == candidate["candidate_id"]
    assert detail["route"]["route_id"] == candidate["route"]["route_id"]
    assert detail["route"]["track_preview"]["point_count"] >= 2
    assert detail["planning_detail"]["summary"]
    assert detail["planning_detail"]["llm_detail_card"]
    assert detail["evidence"]["weather"]["status"] in {"mocked", "unconfirmed"}
    assert "daily_forecast" in detail["evidence"]["weather"]
    assert "current" in detail["evidence"]["weather"]
    assert detail["evidence"]["transport"]["status"] in {"mocked", "unconfirmed"}
    assert "plans" in detail["evidence"]["transport"]
    assert detail["evidence"]["web_evidence"]["status"] == "limited"
    assert detail["evidence"]["web_evidence"]["provider"] == "mock"
    assert detail["evidence"]["web_evidence"]["sources"][0]["url"]
    assert detail["evidence"]["evaluator"]["passed"] is True
    assert detail["evidence"]["evaluator"]["warnings"]


def test_candidate_detail_transport_can_explain_bus_preference_mismatch(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    from app.features.routes import service as route_service

    monkeypatch.setattr(
        route_service,
        "reverse_geocode_wgs84",
        lambda lon, lat: {
            "province": "四川省",
            "city": "甘孜藏族自治州",
            "district": "康定市",
            "display_name": "四川省 · 甘孜藏族自治州 · 康定市",
            "provider": "amap",
            "coordinate_system": "gcj02",
        },
    )
    _upload_public_route(client, auth_headers, name="Cross city route")
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "成都出发，大巴，一日徒步，中等强度"},
    )
    candidate = response.json()["candidate_routes"][0]

    detail_response = client.get(
        f"/api/trip-plans/{response.json()['trip_plan_id']}/candidate-routes/{candidate['candidate_id']}",
        headers=auth_headers,
    )

    transport = detail_response.json()["evidence"]["transport"]
    assert transport["preferred_mode"] == "bus"
    assert transport["recommended_mode"] == "rail_plus_car"
    assert transport["preference_matched"] is False
    assert any(plan["mode"] == "rail_plus_car" for plan in transport["plans"])


def test_closed_trip_plan_rejects_new_messages(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "周末想出去走走"},
    )
    trip_plan_id = response.json()["trip_plan_id"]

    from app.db.session import SessionLocal
    from app.features.trip_plans.model import TripPlan

    db = SessionLocal()
    try:
        trip_plan = db.get(TripPlan, trip_plan_id)
        assert trip_plan is not None
        trip_plan.status = "closed"
        db.add(trip_plan)
        db.commit()
    finally:
        db.close()

    closed_response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"trip_plan_id": trip_plan_id, "content": "再推荐几条"},
    )

    assert closed_response.status_code == 400
    assert closed_response.json()["code"] == "TRIP_PLAN_CLOSED"


def test_user_cannot_access_other_users_agent_run_or_candidate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "trip_other")
    _upload_public_route(client, auth_headers, name="Shared route")
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "成都周边自驾一日徒步，中等强度"},
    )
    candidate = response.json()["candidate_routes"][0]

    events_response = client.get(
        f"/api/agent-runs/{response.json()['agent_run_id']}/events",
        headers=other_headers,
    )
    detail_response = client.get(
        f"/api/trip-plans/{response.json()['trip_plan_id']}/candidate-routes/{candidate['candidate_id']}",
        headers=other_headers,
    )

    assert events_response.status_code == 404
    assert detail_response.status_code == 404
