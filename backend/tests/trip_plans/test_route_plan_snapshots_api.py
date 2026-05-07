from __future__ import annotations

from fastapi.testclient import TestClient

from tests.trip_plans.test_trip_plan_agent_api import _register_and_login, _upload_public_route


def _create_candidate(client: TestClient, headers: dict[str, str]) -> tuple[str, dict]:
    _upload_public_route(client, headers, name="Snapshot candidate")
    response = client.post(
        "/api/trip-plans/messages",
        headers=headers,
        json={"content": "成都周边自驾一日徒步，中等强度"},
    )
    assert response.status_code == 200
    body = response.json()
    return body["trip_plan_id"], body["candidate_routes"][0]


def test_save_candidate_route_creates_snapshot(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    trip_plan_id, candidate = _create_candidate(client, auth_headers)

    response = client.post(
        f"/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate['candidate_id']}/save",
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["snapshot_id"]
    assert body["source_candidate_id"] == candidate["candidate_id"]
    assert body["continue_trip_plan_id"] == trip_plan_id
    assert body["route"]["route_id"] == candidate["route"]["route_id"]
    assert body["route"]["track_preview"]["format"] == "geojson"
    assert body["planning_detail"]["summary"]
    assert body["evidence"]["evaluator"]["passed"] is True


def test_save_candidate_route_rejects_duplicate(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    trip_plan_id, candidate = _create_candidate(client, auth_headers)
    url = f"/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate['candidate_id']}/save"

    first_response = client.post(url, headers=auth_headers)
    second_response = client.post(url, headers=auth_headers)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "ROUTE_PLAN_SNAPSHOT_EXISTS"


def test_list_my_route_plan_snapshots_only_returns_current_user_items(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "snapshot_other")
    trip_plan_id, candidate = _create_candidate(client, auth_headers)
    other_trip_plan_id, other_candidate = _create_candidate(client, other_headers)
    client.post(
        f"/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate['candidate_id']}/save",
        headers=auth_headers,
    )
    client.post(
        f"/api/trip-plans/{other_trip_plan_id}/candidate-routes/{other_candidate['candidate_id']}/save",
        headers=other_headers,
    )

    response = client.get("/api/my/route-plan-snapshots", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["route"]["route_id"] == candidate["route"]["route_id"]


def test_snapshot_detail_returns_saved_route_summary_and_evidence(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    trip_plan_id, candidate = _create_candidate(client, auth_headers)
    save_response = client.post(
        f"/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate['candidate_id']}/save",
        headers=auth_headers,
    )
    snapshot_id = save_response.json()["snapshot_id"]

    response = client.get(
        f"/api/my/route-plan-snapshots/{snapshot_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["snapshot_id"] == snapshot_id
    assert body["route"]["name"] == candidate["route"]["name"]
    assert body["route"]["track_preview"]["point_count"] >= 2
    assert body["planning_detail"]["summary"]
    assert body["evidence"]["weather"]


def test_user_cannot_access_other_users_snapshot(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "snapshot_forbidden")
    trip_plan_id, candidate = _create_candidate(client, auth_headers)
    save_response = client.post(
        f"/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate['candidate_id']}/save",
        headers=auth_headers,
    )
    snapshot_id = save_response.json()["snapshot_id"]

    response = client.get(
        f"/api/my/route-plan-snapshots/{snapshot_id}",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ROUTE_PLAN_SNAPSHOT_NOT_FOUND"
