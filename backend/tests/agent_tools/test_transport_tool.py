from __future__ import annotations

from types import SimpleNamespace


def _mock_settings(use_mock_amap: bool = True):
    return SimpleNamespace(
        use_mock_amap=use_mock_amap,
        amap_web_service_key="test-key" if not use_mock_amap else None,
        amap_reverse_geocode_url="https://restapi.amap.com/v3/geocode/regeo",
    )


def test_transport_tool_public_transport_includes_subway_and_bus_lines(monkeypatch) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(transport, "get_settings", lambda: _mock_settings())

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="成都",
            destination_name="都江堰",
            preferred_mode="public_transport",
            destination_city="成都市",
            cross_city_hint=False,
        )
    )

    assert result.status == "mocked"
    assert result.provider == "mock"
    assert result.preferred_mode == "public_transport"
    assert result.recommended_mode == "public_transport"
    assert result.preference_matched is True
    recommended = result.plans[0]
    assert recommended.mode == "public_transport"
    assert recommended.railway_lines
    assert recommended.bus_lines
    assert recommended.walking_distance_m is not None
    assert recommended.transfer_count is not None
    assert any(step.type == "subway" for step in recommended.steps)


def test_transport_tool_bus_preference_can_recommend_rail_plus_car_for_cross_city(
    monkeypatch,
) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(transport, "get_settings", lambda: _mock_settings())

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="成都",
            destination_name="甘孜藏族自治州康定市",
            preferred_mode="bus",
            destination_city="甘孜藏族自治州",
            route_distance_km=230,
            cross_city_hint=True,
        )
    )

    assert result.status == "mocked"
    assert result.preferred_mode == "bus"
    assert result.recommended_mode == "rail_plus_car"
    assert result.preference_matched is False
    assert result.plans[0].mode == "rail_plus_car"
    assert result.plans[0].feasibility == "recommended"
    assert any(plan.mode == "bus" and plan.feasibility == "limited" for plan in result.plans)
    assert "大巴" in result.summary


def test_transport_tool_self_drive_returns_driving_plan(monkeypatch) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(transport, "get_settings", lambda: _mock_settings())

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="成都",
            destination_name="线路起点",
            preferred_mode="self_drive",
            route_distance_km=80,
        )
    )

    assert result.recommended_mode == "self_drive"
    assert result.preference_matched is True
    assert result.plans[0].mode == "self_drive"
    assert result.plans[0].driving_distance_km is not None
    assert result.plans[0].duration_minutes is not None


def test_transport_tool_real_amap_driving_parses_path(monkeypatch) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(transport, "get_settings", lambda: _mock_settings(False))
    monkeypatch.setattr(transport.httpx, "Client", FakeAmapClient)

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="深圳",
            destination_coordinate=transport.Coordinate(lon=114.123, lat=22.456),
            preferred_mode="self_drive",
        )
    )

    assert result.status == "confirmed"
    assert result.provider == "amap"
    assert result.recommended_mode == "self_drive"
    assert result.plans[0].mode == "self_drive"
    assert result.plans[0].distance_km == 36.5
    assert result.plans[0].duration_minutes == 61
    assert result.plans[0].tolls_cny == 12
    assert result.raw["geocode_origin"]["status"] == "1"
    assert result.raw["driving"]["status"] == "1"


def test_transport_tool_real_amap_transit_extracts_subway_and_railway(monkeypatch) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(transport, "get_settings", lambda: _mock_settings(False))
    monkeypatch.setattr(transport.httpx, "Client", FakeAmapClient)

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="深圳",
            destination_coordinate=transport.Coordinate(lon=114.123, lat=22.456),
            preferred_mode="public_transport",
            destination_city="深圳市",
        )
    )

    assert result.status == "confirmed"
    assert result.recommended_mode == "public_transport"
    plan = result.plans[0]
    assert plan.duration_minutes == 90
    assert "地铁2号线" in plan.bus_lines
    assert "城际铁路C123" in plan.railway_lines
    assert any(step.type == "subway" for step in plan.steps)
    assert any(step.type == "railway" for step in plan.steps)


def test_transport_tool_real_provider_missing_key_degrades(monkeypatch) -> None:
    from app.features.agent_tools import transport

    monkeypatch.setattr(
        transport,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=False,
            amap_web_service_key=None,
            amap_reverse_geocode_url="https://restapi.amap.com/v3/geocode/regeo",
        ),
    )

    result = transport.get_transport_evidence(
        transport.TransportRequest(
            origin_name="成都",
            destination_name="线路起点",
            preferred_mode="self_drive",
        )
    )

    assert result.status == "unconfirmed"
    assert result.provider == "amap"
    assert result.plans == []


class FakeAmapClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def get(self, url: str, params: dict):
        if url.endswith("/v3/geocode/geo"):
            return FakeResponse(
                {
                    "status": "1",
                    "geocodes": [
                        {
                            "formatted_address": "深圳市",
                            "location": "114.057868,22.543099",
                        }
                    ],
                }
            )
        if url.endswith("/v3/direction/driving"):
            return FakeResponse(
                {
                    "status": "1",
                    "route": {
                        "paths": [
                            {
                                "distance": "36500",
                                "duration": "3660",
                                "tolls": "12",
                                "steps": [
                                    {"instruction": "沿主路行驶"},
                                    {"instruction": "到达目的地"},
                                ],
                            }
                        ]
                    },
                }
            )
        if url.endswith("/v3/direction/transit/integrated"):
            return FakeResponse(
                {
                    "status": "1",
                    "route": {
                        "transits": [
                            {
                                "duration": "5400",
                                "walking_distance": "800",
                                "segments": [
                                    {
                                        "bus": {
                                            "buslines": [
                                                {
                                                    "name": "地铁2号线",
                                                    "type": "地铁线路",
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "railway": {
                                            "name": "城际铁路C123",
                                        }
                                    },
                                ],
                            }
                        ]
                    },
                }
            )
        raise AssertionError(url)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload
