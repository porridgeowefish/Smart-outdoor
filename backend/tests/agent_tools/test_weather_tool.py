from __future__ import annotations

from types import SimpleNamespace


def test_weather_tool_mock_returns_qweather_aligned_schema(monkeypatch) -> None:
    from app.features.agent_tools import weather

    monkeypatch.setattr(
        weather,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_weather=True,
            qweather_api_key=None,
            weather_developer_host="devapi.qweather.com",
        ),
    )

    result = weather.get_weather_evidence(
        weather.WeatherRequest(
            lon=101.9603225,
            lat=30.0260438,
            location_name="四川省 · 甘孜藏族自治州 · 康定市",
            days=3,
        )
    )

    assert result.status == "mocked"
    assert result.provider == "mock"
    assert result.current is not None
    assert result.current.temp is not None
    assert result.current.text
    assert len(result.daily_forecast) == 3
    assert result.daily_forecast[0].fx_date
    assert result.hourly_forecast
    assert result.warnings == []
    assert result.raw == {}


def test_weather_tool_returns_unconfirmed_for_invalid_coordinate(monkeypatch) -> None:
    from app.features.agent_tools import weather

    monkeypatch.setattr(
        weather,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_weather=True,
            qweather_api_key=None,
            weather_developer_host="devapi.qweather.com",
        ),
    )

    result = weather.get_weather_evidence(
        weather.WeatherRequest(lon=200, lat=30, location_name="invalid")
    )

    assert result.status == "unconfirmed"
    assert result.provider == "mock"
    assert "坐标" in result.summary


def test_weather_tool_real_qweather_parses_current_daily_and_hourly(monkeypatch) -> None:
    from app.features.agent_tools import weather

    monkeypatch.setattr(
        weather,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_weather=False,
            qweather_api_key="test-key",
            weather_developer_host="devapi.qweather.com",
        ),
    )
    monkeypatch.setattr(weather.httpx, "Client", FakeWeatherClient)

    result = weather.get_weather_evidence(
        weather.WeatherRequest(lon=101.9603225, lat=30.0260438, days=3)
    )

    assert result.status == "confirmed"
    assert result.provider == "qweather"
    assert result.current is not None
    assert result.current.text == "多云"
    assert result.current.temp == 12
    assert len(result.daily_forecast) == 3
    assert result.daily_forecast[0].text_day == "晴"
    assert result.hourly_forecast[0].pop == 20
    assert "QWeather" in result.summary


def test_weather_tool_real_provider_missing_key_degrades(monkeypatch) -> None:
    from app.features.agent_tools import weather

    monkeypatch.setattr(
        weather,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_weather=False,
            qweather_api_key=None,
            weather_developer_host="devapi.qweather.com",
        ),
    )

    result = weather.get_weather_evidence(
        weather.WeatherRequest(lon=101.9603225, lat=30.0260438)
    )

    assert result.status == "unconfirmed"
    assert result.provider == "qweather"
    assert result.current is None


class FakeWeatherClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def get(self, url: str, params: dict):
        if url.endswith("/now"):
            return FakeResponse(
                {
                    "code": "200",
                    "updateTime": "2026-05-06T10:00+08:00",
                    "now": {
                        "obsTime": "2026-05-06T10:00+08:00",
                        "temp": "12",
                        "feelsLike": "11",
                        "text": "多云",
                        "windDir": "西南风",
                        "windScale": "3",
                        "humidity": "65",
                        "precip": "0.0",
                        "vis": "10",
                    },
                }
            )
        if url.endswith("/3d"):
            return FakeResponse(
                {
                    "code": "200",
                    "daily": [
                        {
                            "fxDate": "2026-05-06",
                            "tempMax": "18",
                            "tempMin": "8",
                            "textDay": "晴",
                            "textNight": "多云",
                            "windScaleDay": "3-4",
                            "precip": "0",
                            "uvIndex": "5",
                        },
                        {
                            "fxDate": "2026-05-07",
                            "tempMax": "19",
                            "tempMin": "9",
                            "textDay": "多云",
                        },
                        {
                            "fxDate": "2026-05-08",
                            "tempMax": "20",
                            "tempMin": "10",
                            "textDay": "阴",
                        },
                    ],
                }
            )
        if url.endswith("/24h"):
            return FakeResponse(
                {
                    "code": "200",
                    "hourly": [
                        {
                            "fxTime": "2026-05-06T11:00+08:00",
                            "temp": "13",
                            "text": "多云",
                            "windScale": "3",
                            "pop": "20",
                            "precip": "0",
                        }
                    ],
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
