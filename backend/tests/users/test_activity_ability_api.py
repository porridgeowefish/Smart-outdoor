from __future__ import annotations

from fastapi.testclient import TestClient


TIMED_GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="30.000000" lon="104.000000"><ele>100</ele><time>2026-05-01T00:00:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.010000"><ele>300</ele><time>2026-05-01T00:20:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.020000"><ele>560</ele><time>2026-05-01T00:39:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""


LONG_CLIMB_GPX = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="30.000000" lon="104.000000"><ele>100</ele><time>2026-05-03T00:00:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.090000"><ele>1300</ele><time>2026-05-03T02:40:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.180000"><ele>2500</ele><time>2026-05-03T05:20:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.240000"><ele>3500</ele><time>2026-05-03T08:00:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""


def test_get_ability_profile_returns_404_without_activity(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/me/ability-profile", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "ABILITY_PROFILE_NOT_FOUND"


def test_upload_activity_track_creates_track_and_profile(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/me/activity-tracks/upload",
        headers=auth_headers,
        data={"activity_date": "2026-05-01", "source_type": "manual_upload"},
        files={"file": ("wutong.gpx", TIMED_GPX, "application/gpx+xml")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["activity_track_id"]
    assert body["parse_status"] == "parsed"
    assert body["analysis"]["distance_km"] > 1
    assert body["analysis"]["moving_time_seconds"] == 2340

    profile = body["ability_profile"]
    assert profile["activity_count"] == 1
    assert profile["confidence"] == "low"
    assert 0 < profile["endurance_score"] <= 1
    assert 0 < profile["climb_score"] <= 1
    assert profile["metrics_json"]["algorithm_version"] == "ability_v1"
    assert profile["metrics_json"]["best_vam_20min_m_per_h"] > 500


def test_upload_activity_track_stores_reverse_geocoded_location(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    from app.features.users import activity_service

    monkeypatch.setattr(
        activity_service,
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

    response = client.post(
        "/api/me/activity-tracks/upload",
        headers=auth_headers,
        files={"file": ("coros.gpx", TIMED_GPX, "application/gpx+xml")},
    )
    list_response = client.get("/api/me/activity-tracks", headers=auth_headers)

    assert response.status_code == 200
    assert list_response.status_code == 200
    assert list_response.json()["tracks"][0]["location"] == "四川省 · 甘孜藏族自治州 · 康定市"


def test_activity_list_groups_by_month_and_profile_accumulates(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for filename, content, activity_date in [
        ("wutong.gpx", TIMED_GPX, "2026-05-01"),
        ("emei.gpx", LONG_CLIMB_GPX, "2026-05-03"),
    ]:
        response = client.post(
            "/api/me/activity-tracks/upload",
            headers=auth_headers,
            data={"activity_date": activity_date},
            files={"file": (filename, content, "application/gpx+xml")},
        )
        assert response.status_code == 200

    list_response = client.get("/api/me/activity-tracks", headers=auth_headers)

    assert list_response.status_code == 200
    tracks = list_response.json()["tracks"]
    assert len(tracks) == 2
    assert tracks[0]["month"] == "5"
    assert tracks[0]["location"] == "待识别"
    assert tracks[0]["activity_date"] in {"2026-05-01", "2026-05-03"}
    assert tracks[0]["analysis_json"]["effort_km"] > tracks[0]["distance_km"]

    profile_response = client.get("/api/me/ability-profile", headers=auth_headers)
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["activity_count"] == 2
    assert profile["confidence"] == "medium"
    assert "当前能力画像" in profile["message"]
    assert profile["recent_max_elevation_gain_m"] >= 3400
    assert profile["metrics_json"]["best_vam_60min_m_per_h"] > 0
    assert len(profile["generated_from_activity_track_ids"]) == 2


def test_upload_activity_rejects_invalid_file_type(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/me/activity-tracks/upload",
        headers=auth_headers,
        files={"file": ("activity.txt", b"not a track", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "UNSUPPORTED_FILE_TYPE"
