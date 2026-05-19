from __future__ import annotations

from fastapi.testclient import TestClient

from tests.routes.test_route_upload_api import VALID_GPX
from tests.routes.upload_helpers import upload_route_complete


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


def _upload_route(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    visibility: str = "private",
    manual_tags: dict | None = None,
) -> str:
    body = upload_route_complete(
        client,
        headers,
        name=name,
        description=f"{name} description",
        visibility=visibility,
        manual_tags=manual_tags or {},
        content=VALID_GPX,
        filename=f"{name}.gpx",
    )
    assert body["parse_status"] == "parsed"
    return body["route_id"]


def test_list_routes_requires_authorization(client: TestClient) -> None:
    response = client.get("/api/routes")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_list_routes_returns_public_and_current_user_private_only(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "other_user")
    current_private_id = _upload_route(
        client, auth_headers, name="Current private route", visibility="private"
    )
    current_public_id = _upload_route(
        client, auth_headers, name="Current public route", visibility="public"
    )
    other_public_id = _upload_route(
        client, other_headers, name="Other public route", visibility="public"
    )
    other_private_id = _upload_route(
        client, other_headers, name="Other private route", visibility="private"
    )

    response = client.get("/api/routes", headers=auth_headers)

    assert response.status_code == 200
    items = response.json()["items"]
    route_ids = {item["route_id"] for item in items}
    assert current_private_id in route_ids
    assert current_public_id in route_ids
    assert other_public_id in route_ids
    assert other_private_id not in route_ids
    assert response.json()["pagination"]["total"] == 3


def test_list_routes_filters_by_tags(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    forest_id = _upload_route(
        client,
        auth_headers,
        name="Forest route",
        visibility="private",
        manual_tags={"scenery": ["forest"], "transport": ["self-drive friendly"]},
    )
    river_id = _upload_route(
        client,
        auth_headers,
        name="River route",
        visibility="private",
        manual_tags={"scenery": ["river"]},
    )

    any_response = client.get(
        "/api/routes?tags=forest,river&tag_match_mode=any",
        headers=auth_headers,
    )
    all_response = client.get(
        "/api/routes?tags=forest,self-drive friendly&tag_match_mode=all",
        headers=auth_headers,
    )

    assert any_response.status_code == 200
    assert {item["route_id"] for item in any_response.json()["items"]} == {
        forest_id,
        river_id,
    }
    assert all_response.status_code == 200
    assert [item["route_id"] for item in all_response.json()["items"]] == [forest_id]


def test_get_route_detail_returns_analysis_track_and_primary_file(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    route_id = _upload_route(
        client,
        auth_headers,
        name="Detail route",
        visibility="private",
        manual_tags={"scenery": ["forest"], "transport": ["self-drive friendly"]},
    )

    response = client.get(f"/api/routes/{route_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["route_id"] == route_id
    assert data["name"] == "Detail route"
    assert data["visibility"] == "private"
    assert data["manual_tags"]["scenery"] == ["forest"]
    assert data["location"] == "待识别"
    assert data["analysis"]["distance_km"] > 0
    assert data["analysis"]["elevation_gain_m"] == 15
    assert data["track_preview"]["format"] == "geojson"
    assert data["track"]["format"] == "geojson"
    assert data["track"]["coordinate_system"] == "wgs84"
    assert data["track"]["track_url"] == f"/api/routes/{route_id}/track"
    track_response = client.get(data["track"]["track_url"], headers=auth_headers)
    assert track_response.status_code == 200
    assert track_response.json()["geojson"]["type"] == "LineString"
    assert track_response.json()["point_count"] >= data["analysis"]["distance_km"] * 100
    assert data["primary_file"]["file_type"] == "gpx"
    assert data["primary_file"]["parse_status"] == "parsed"
    assert data["actions"]["can_send_to_trip_plan"] is True
    assert data["actions"]["can_edit"] is True


def test_route_location_can_come_from_manual_tags(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    route_id = _upload_route(
        client,
        auth_headers,
        name="Location route",
        visibility="private",
        manual_tags={"location": ["四川省", "甘孜藏族自治州"]},
    )

    list_response = client.get("/api/routes", headers=auth_headers)
    detail_response = client.get(f"/api/routes/{route_id}", headers=auth_headers)

    assert list_response.status_code == 200
    item = next(
        item for item in list_response.json()["items"] if item["route_id"] == route_id
    )
    assert item["location"] == "四川省 · 甘孜藏族自治州"
    assert detail_response.status_code == 200
    assert detail_response.json()["location"] == "四川省 · 甘孜藏族自治州"


def test_get_route_detail_hides_other_user_private_route(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "other_user")
    route_id = _upload_route(
        client, other_headers, name="Other private detail", visibility="private"
    )

    response = client.get(f"/api/routes/{route_id}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {
        "code": "ROUTE_NOT_FOUND",
        "message": "Route not found",
    }


def test_get_route_detail_allows_other_user_public_route(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    other_headers = _register_and_login(client, "other_user")
    route_id = _upload_route(
        client, other_headers, name="Other public detail", visibility="public"
    )

    response = client.get(f"/api/routes/{route_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["route_id"] == route_id
    assert response.json()["actions"]["can_edit"] is False


def test_openapi_exposes_route_list_and_detail(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/routes" in paths
    assert "/api/routes/{route_id}" in paths
