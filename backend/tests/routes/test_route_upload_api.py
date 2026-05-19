from __future__ import annotations

from fastapi.testclient import TestClient

from tests.routes.upload_helpers import image_asset, post_route_complete, upload_route_complete

VALID_GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk>
    <name>Demo Track</name>
    <trkseg>
      <trkpt lat="30.000000" lon="104.000000"><ele>100</ele></trkpt>
      <trkpt lat="30.000000" lon="104.001000"><ele>115</ele></trkpt>
      <trkpt lat="30.000000" lon="104.002000"><ele>110</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
"""


def test_upload_route_requires_authorization(client: TestClient) -> None:
    response = client.post("/api/routes/upload", json={})

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_upload_route_rejects_unsupported_file_type(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = post_route_complete(
        client,
        auth_headers,
        name="Demo route",
        content=b"not a track",
        filename="demo.txt",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "UNSUPPORTED_FILE_TYPE",
        "message": "Only GPX, KML, and GeoJSON route files are supported",
    }


def test_upload_route_rejects_invalid_manual_tags_payload(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = post_route_complete(
        client,
        auth_headers,
        name="Demo route",
        content=VALID_GPX,
        manual_tags="not-a-dict",  # type: ignore[arg-type]
    )

    assert response.status_code == 422


def test_route_tag_taxonomy_returns_multidimensional_categories(
    client: TestClient,
) -> None:
    response = client.get("/api/routes/tag-taxonomy")

    assert response.status_code == 200
    categories = {item["key"]: item for item in response.json()["categories"]}
    assert "supply" in categories
    assert "terrain" in categories
    assert "scenery" in categories
    assert "有小卖部" in categories["supply"]["tags"]
    assert "台阶路/阶梯路" in categories["terrain"]["tags"]
    assert "雪山" in categories["scenery"]["tags"]


def test_upload_gpx_route_creates_asset_file_and_analysis(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    manual_tags = {
        "transport": ["self-drive friendly"],
        "scenery": ["forest", "river"],
    }
    body = upload_route_complete(
        client,
        auth_headers,
        name="Demo GPX route",
        description="A short demo route",
        visibility="private",
        manual_tags=manual_tags,
        content=VALID_GPX,
    )

    assert body["route_id"]
    assert body["file_id"]
    assert body["parse_status"] == "parsed"
    assert body["parse_error"] is None

    from app.db.session import SessionLocal
    from app.features.routes.model import (
        RouteAnalysisSnapshot,
        RouteAsset,
        RouteFile,
    )

    db = SessionLocal()
    try:
        route = db.get(RouteAsset, body["route_id"])
        route_file = db.get(RouteFile, body["file_id"])
        analysis = (
            db.query(RouteAnalysisSnapshot)
            .filter(RouteAnalysisSnapshot.route_asset_id == body["route_id"])
            .one()
        )
    finally:
        db.close()

    assert route is not None
    assert route.name == "Demo GPX route"
    assert route.description == "A short demo route"
    assert route.visibility == "private"
    assert route.manual_tags == manual_tags
    assert route.source_type == "user_upload"

    assert route_file is not None
    assert route_file.file_type == "gpx"
    assert route_file.parse_status == "parsed"
    assert route_file.file_url.endswith(".gpx")
    assert route_file.storage_provider == "local"
    assert route_file.storage_key
    assert route_file.content_type == "application/gpx+xml"
    assert route_file.original_filename == "demo.gpx"

    assert analysis.distance_km > 0
    assert analysis.elevation_gain_m == 15
    assert analysis.elevation_loss_m == 5
    assert analysis.elevation_min_m == 100
    assert analysis.elevation_max_m == 115
    assert analysis.start_point == {"lon": 104.0, "lat": 30.0, "ele": 100.0}
    assert analysis.end_point == {"lon": 104.002, "lat": 30.0, "ele": 110.0}
    assert analysis.track_preview_geojson["type"] == "LineString"
    assert analysis.track_preview_geojson["coordinates"][0] == [104.0, 30.0, 100.0]
    assert analysis.track_preview_geojson["coordinates"][-1] == [104.002, 30.0, 110.0]
    assert analysis.track_geojson_storage_key
    assert analysis.track_geojson_point_count >= analysis.distance_km * 100
    assert analysis.analysis_json["preview_tolerance_m"] == 10

    list_response = client.get("/api/routes", headers=auth_headers)
    item = next(
        item for item in list_response.json()["items"] if item["route_id"] == body["route_id"]
    )
    assert item["track_preview"]["format"] == "geojson"
    assert item["track_preview"]["coordinate_system"] == "wgs84"
    assert item["track_preview"]["point_count"] >= 3
    assert len(item["track_preview"]["geojson"]["coordinates"]) >= 2


def test_upload_route_stores_multidimensional_manual_tags(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    manual_tags = {
        "supply": ["有小卖部", "有饮用水"],
        "transport_facility": ["停车场", "自驾友好"],
        "terrain": ["台阶路/阶梯路", "碎石路/乱石路"],
        "scenery": ["森林", "溪流"],
        "audience": ["摄影友好"],
    }

    body = upload_route_complete(
        client,
        auth_headers,
        name="Tagged route",
        manual_tags=manual_tags,
        content=VALID_GPX,
    )
    detail_response = client.get(
        f"/api/routes/{body['route_id']}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["manual_tags"] == manual_tags
    assert "有小卖部" in detail["manual_tags"]["supply"]


def test_upload_route_accepts_cover_image(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    cover = image_asset(
        client,
        auth_headers,
        asset_type="route_cover",
        original_filename="cover.jpg",
        variants={
            "large": (b"large-webp", 1280, 720),
            "thumbnail": (b"thumb-webp", 480, 270),
        },
    )
    body = upload_route_complete(
        client,
        auth_headers,
        name="Route with cover",
        content=VALID_GPX,
        cover_image=cover,
    )

    from app.db.session import SessionLocal
    from app.features.routes.model import RouteAsset

    db = SessionLocal()
    try:
        route = db.get(RouteAsset, body["route_id"])
    finally:
        db.close()

    assert route is not None
    assert route.cover_image_url is not None
    assert route.cover_image_url.startswith("/static/assets/")
    assert route.cover_image_url.endswith(".webp")
    assert route.cover_image_variants["thumbnail"]["url"].endswith(".webp")


def test_upload_route_stores_reverse_geocoded_location(
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

    body = upload_route_complete(
        client,
        auth_headers,
        name="Route with location",
        content=VALID_GPX,
    )
    list_response = client.get("/api/routes", headers=auth_headers)
    route_id = body["route_id"]
    item = next(
        item for item in list_response.json()["items"] if item["route_id"] == route_id
    )
    assert item["location"] == "四川省 · 甘孜藏族自治州 · 康定市"


def test_upload_route_rejects_non_image_cover(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = post_route_complete(
        client,
        auth_headers,
        name="Route with bad cover",
        content=VALID_GPX,
        cover_image={
            "storage_provider": "local",
            "storage_key": "not-owned/cover.webp",
            "url": "/static/assets/not-owned/cover.webp",
            "original_filename": "cover.txt",
            "processing_status": "ready",
            "variants": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_STORAGE_OBJECT"


def test_upload_route_defaults_to_private_visibility(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = upload_route_complete(
        client,
        auth_headers,
        name="Default private route",
        content=VALID_GPX,
    )

    from app.db.session import SessionLocal
    from app.features.routes.model import RouteAsset

    db = SessionLocal()
    try:
        route = db.get(RouteAsset, body["route_id"])
    finally:
        db.close()

    assert route is not None
    assert route.visibility == "private"


def test_upload_malformed_track_marks_file_failed(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = post_route_complete(
        client,
        auth_headers,
        name="Broken route",
        filename="broken.gpx",
        content=b"<gpx><broken>",
        content_type="application/gpx+xml",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route_id"]
    assert body["file_id"]
    assert body["parse_status"] == "failed"
    assert body["parse_error"] == "TRACK_PARSE_FAILED"

    from app.db.session import SessionLocal
    from app.features.routes.model import RouteAnalysisSnapshot, RouteFile

    db = SessionLocal()
    try:
        route_file = db.get(RouteFile, body["file_id"])
        analysis_count = (
            db.query(RouteAnalysisSnapshot)
            .filter(RouteAnalysisSnapshot.route_asset_id == body["route_id"])
            .count()
        )
    finally:
        db.close()

    assert route_file is not None
    assert route_file.parse_status == "failed"
    assert route_file.parse_error == "TRACK_PARSE_FAILED"
    assert analysis_count == 0
