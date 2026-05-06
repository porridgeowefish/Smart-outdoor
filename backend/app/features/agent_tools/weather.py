from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings

WeatherStatus = Literal["mocked", "confirmed", "unconfirmed", "unavailable"]


class WeatherRequest(BaseModel):
    lon: float
    lat: float
    location_name: str | None = None
    days: int = Field(default=3, ge=1, le=7)


class CurrentWeather(BaseModel):
    observed_at: str | None = None
    temp: float | None = None
    feels_like: float | None = None
    text: str
    wind_dir: str | None = None
    wind_scale: str | None = None
    humidity: int | None = None
    precip: float | None = None
    visibility_km: float | None = None


class DailyWeather(BaseModel):
    fx_date: str
    temp_max: float | None = None
    temp_min: float | None = None
    text_day: str
    text_night: str | None = None
    wind_scale_day: str | None = None
    precip: float | None = None
    uv_index: int | None = None


class HourlyWeather(BaseModel):
    fx_time: str
    temp: float | None = None
    text: str
    wind_scale: str | None = None
    pop: int | None = None
    precip: float | None = None


class WeatherEvidence(BaseModel):
    status: WeatherStatus
    provider: str
    summary: str
    current: CurrentWeather | None = None
    daily_forecast: list[DailyWeather] = Field(default_factory=list)
    hourly_forecast: list[HourlyWeather] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


def get_weather_evidence(payload: WeatherRequest) -> WeatherEvidence:
    if not _valid_coordinate(payload.lon, payload.lat):
        return WeatherEvidence(
            status="unconfirmed",
            provider="mock",
            summary="坐标无效，天气未确认。",
        )

    settings = get_settings()
    if settings.use_mock_weather:
        return _mock_weather(payload)

    if not settings.qweather_api_key:
        return WeatherEvidence(
            status="unconfirmed",
            provider="qweather",
            summary="未配置 QWeather API Key，天气未确认。",
        )

    return _qweather(payload, settings.weather_developer_host, settings.qweather_api_key)


def weather_evidence_json(payload: WeatherRequest) -> dict[str, Any]:
    return get_weather_evidence(payload).model_dump()


def _qweather(payload: WeatherRequest, host: str, api_key: str) -> WeatherEvidence:
    location = f"{payload.lon:.6f},{payload.lat:.6f}"
    base_url = f"https://{host.rstrip('/')}"
    headers = {"Accept": "application/json", "X-QW-Api-Key": api_key}
    warnings: list[str] = []
    raw: dict[str, Any] = {}

    try:
        with httpx.Client(timeout=8.0, headers=headers, trust_env=False) as client:
            now_raw = _qweather_get(
                client,
                f"{base_url}/v7/weather/now",
                {"location": location, "key": api_key},
            )
            raw["now"] = now_raw
            current = _parse_current(now_raw)

            daily_path = "7d" if payload.days > 3 else "3d"
            try:
                daily_raw = _qweather_get(
                    client,
                    f"{base_url}/v7/weather/{daily_path}",
                    {"location": location, "key": api_key},
                )
                raw["daily"] = daily_raw
                daily = _parse_daily(daily_raw)[: payload.days]
            except ToolRequestError as exc:
                warnings.append(f"逐日天气未确认：{exc}")
                daily = []

            try:
                hourly_raw = _qweather_get(
                    client,
                    f"{base_url}/v7/weather/24h",
                    {"location": location, "key": api_key},
                )
                raw["hourly"] = hourly_raw
                hourly = _parse_hourly(hourly_raw)[:8]
            except ToolRequestError as exc:
                warnings.append(f"逐小时天气未确认：{exc}")
                hourly = []
    except (httpx.HTTPError, ToolRequestError) as exc:
        return WeatherEvidence(
            status="unconfirmed",
            provider="qweather",
            summary=f"QWeather 调用失败，天气未确认：{exc}",
            warnings=[str(exc)],
            raw=raw,
        )

    return WeatherEvidence(
        status="confirmed",
        provider="qweather",
        summary=_weather_summary(payload, current, daily),
        current=current,
        daily_forecast=daily,
        hourly_forecast=hourly,
        warnings=warnings,
        raw=raw,
    )


def _qweather_get(
    client: httpx.Client,
    url: str,
    params: dict[str, str],
) -> dict[str, Any]:
    response = client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if str(data.get("code")) != "200":
        raise ToolRequestError(f"code={data.get('code')}")
    return data


def _parse_current(data: dict[str, Any]) -> CurrentWeather:
    now = data.get("now") or {}
    return CurrentWeather(
        observed_at=str(now.get("obsTime") or data.get("updateTime") or ""),
        temp=_float_or_none(now.get("temp")),
        feels_like=_float_or_none(now.get("feelsLike")),
        text=str(now.get("text") or "未确认"),
        wind_dir=_str_or_none(now.get("windDir")),
        wind_scale=_str_or_none(now.get("windScale")),
        humidity=_int_or_none(now.get("humidity")),
        precip=_float_or_none(now.get("precip")),
        visibility_km=_float_or_none(now.get("vis")),
    )


def _parse_daily(data: dict[str, Any]) -> list[DailyWeather]:
    items = data.get("daily")
    if not isinstance(items, list):
        return []
    return [
        DailyWeather(
            fx_date=str(item.get("fxDate") or ""),
            temp_max=_float_or_none(item.get("tempMax")),
            temp_min=_float_or_none(item.get("tempMin")),
            text_day=str(item.get("textDay") or "未确认"),
            text_night=_str_or_none(item.get("textNight")),
            wind_scale_day=_str_or_none(item.get("windScaleDay")),
            precip=_float_or_none(item.get("precip")),
            uv_index=_int_or_none(item.get("uvIndex")),
        )
        for item in items
        if isinstance(item, dict)
    ]


def _parse_hourly(data: dict[str, Any]) -> list[HourlyWeather]:
    items = data.get("hourly")
    if not isinstance(items, list):
        return []
    return [
        HourlyWeather(
            fx_time=str(item.get("fxTime") or ""),
            temp=_float_or_none(item.get("temp")),
            text=str(item.get("text") or "未确认"),
            wind_scale=_str_or_none(item.get("windScale")),
            pop=_int_or_none(item.get("pop")),
            precip=_float_or_none(item.get("precip")),
        )
        for item in items
        if isinstance(item, dict)
    ]


def _weather_summary(
    payload: WeatherRequest,
    current: CurrentWeather,
    daily: list[DailyWeather],
) -> str:
    place = payload.location_name or f"{payload.lon:.3f},{payload.lat:.3f}"
    if daily:
        first = daily[0]
        return (
            f"{place} 天气已由 QWeather 确认：当前{current.text}"
            f"{_format_temp(current.temp)}；{first.fx_date} 白天{first.text_day}，"
            f"{_format_range(first.temp_min, first.temp_max)}。出发前仍建议复核临近预报。"
        )
    return (
        f"{place} 天气已由 QWeather 确认：当前{current.text}"
        f"{_format_temp(current.temp)}。出发前仍建议复核临近预报。"
    )


def _mock_weather(payload: WeatherRequest) -> WeatherEvidence:
    today = date.today()
    place = payload.location_name or f"{payload.lon:.3f},{payload.lat:.3f}"
    daily = [
        DailyWeather(
            fx_date=today.isoformat(),
            temp_max=18,
            temp_min=8,
            text_day="多云",
            text_night="多云",
            wind_scale_day="3-4",
            precip=0,
            uv_index=5,
        )
    ]
    for offset in range(1, payload.days):
        item_date = date.fromordinal(today.toordinal() + offset)
        daily.append(
            DailyWeather(
                fx_date=item_date.isoformat(),
                temp_max=17 + offset,
                temp_min=7 + offset,
                text_day="多云",
                text_night="阴",
                wind_scale_day="3-4",
                precip=0,
                uv_index=4,
            )
        )

    now = datetime.now(timezone.utc).replace(microsecond=0)
    hourly = [
        HourlyWeather(
            fx_time=now.isoformat(),
            temp=12,
            text="多云",
            wind_scale="3",
            pop=20,
            precip=0,
        )
    ]

    return WeatherEvidence(
        status="mocked",
        provider="mock",
        summary=f"{place} 天气为 mock 数据：多云，气温约 8-18°C。出发前需要查询真实天气。",
        current=CurrentWeather(
            observed_at=now.isoformat(),
            temp=12,
            feels_like=11,
            text="多云",
            wind_dir="西南风",
            wind_scale="3",
            humidity=65,
            precip=0,
            visibility_km=10,
        ),
        daily_forecast=daily,
        hourly_forecast=hourly,
        warnings=[],
        raw={},
    )


def _format_temp(value: float | None) -> str:
    if value is None:
        return ""
    return f"，{value:g}°C"


def _format_range(low: float | None, high: float | None) -> str:
    if low is None or high is None:
        return "温度未确认"
    return f"{low:g}-{high:g}°C"


def _valid_coordinate(lon: float, lat: float) -> bool:
    return -180 <= lon <= 180 and -90 <= lat <= 90


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class ToolRequestError(Exception):
    pass
