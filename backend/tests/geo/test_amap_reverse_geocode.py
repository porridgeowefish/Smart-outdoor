from __future__ import annotations

import json
from types import SimpleNamespace


def test_wgs84_to_gcj02_converts_mainland_china_coordinate() -> None:
    from app.features.geo.amap_reverse_geocode import wgs84_to_gcj02

    lon, lat = wgs84_to_gcj02(116.397, 39.908)

    assert abs(lon - 116.4032) < 0.01
    assert abs(lat - 39.9094) < 0.01


def test_reverse_geocode_returns_none_without_key(monkeypatch) -> None:
    from app.features.geo import amap_reverse_geocode as service

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=False,
            amap_web_service_key=None,
            amap_reverse_geocode_url="https://restapi.amap.com/v3/geocode/regeo",
        ),
    )

    assert service.reverse_geocode_wgs84(116.397, 39.908) is None


def test_reverse_geocode_parses_amap_response(monkeypatch) -> None:
    from app.features.geo import amap_reverse_geocode as service

    captured_url = ""

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "status": "1",
                    "info": "OK",
                    "regeocode": {
                        "formatted_address": "四川省甘孜藏族自治州康定市某地",
                        "addressComponent": {
                            "province": "四川省",
                            "city": "甘孜藏族自治州",
                            "district": "康定市",
                            "adcode": "513301",
                        },
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(url: str, timeout: int):
        nonlocal captured_url
        captured_url = url
        return FakeResponse()

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=False,
            amap_web_service_key="test-key",
            amap_reverse_geocode_url="https://restapi.amap.com/v3/geocode/regeo",
        ),
    )
    monkeypatch.setattr(service.request, "urlopen", fake_urlopen)

    result = service.reverse_geocode_wgs84(101.9603225, 30.0260438)

    assert result == {
        "province": "四川省",
        "city": "甘孜藏族自治州",
        "district": "康定市",
        "adcode": "513301",
        "formatted_address": "四川省甘孜藏族自治州康定市某地",
        "display_name": "四川省 · 甘孜藏族自治州 · 康定市",
        "provider": "amap",
        "coordinate_system": "gcj02",
    }
    assert "key=test-key" in captured_url
    assert "location=" in captured_url
