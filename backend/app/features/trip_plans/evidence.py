from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from app.features.agent_tools.search import SearchRequest, search_evidence_json
from app.features.agent_tools.transport import TransportRequest, transport_evidence_json
from app.features.agent_tools.weather import WeatherRequest, weather_evidence_json
from app.features.llm.provider import AgentLLMProvider
from app.features.llm.schemas import ResponseGenerationInput
from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.router import _route_location
from app.features.trip_plans.context import geo_raw_text

logger = logging.getLogger(__name__)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:1[3-9]\d{9}|0\d{2,3}[- ]?\d{7,8}|400[- ]?\d{3}[- ]?\d{4}|(?:110|119|120|12122|12345|12315))(?!\d)"
)


def candidate_evidence(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict,
    llm_provider: AgentLLMProvider | None = None,
) -> dict:
    tasks: dict[str, Callable[[], dict]] = {
        "weather": lambda: weather_for_route(route, analysis),
        "transport": lambda: transport_for_route(route, analysis, context_state),
        "web_evidence": lambda: search_for_route(route, analysis, context_state),
    }
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            name: executor.submit(_safe_call, name, fn)
            for name, fn in tasks.items()
        }
        weather = futures["weather"].result()
        transport = futures["transport"].result()
        web_evidence = futures["web_evidence"].result()

    weather = enrich_weather_for_route(weather, analysis)
    web_evidence = summarize_web_evidence(
        route,
        analysis,
        context_state,
        web_evidence,
        llm_provider,
    )
    return {"weather": weather, "transport": transport, "web_evidence": web_evidence}


def _safe_call(tool_name: str, fn: callable) -> dict:
    try:
        return fn()
    except Exception as exc:
        logger.exception("Evidence tool %s failed", tool_name)
        return {
            "status": "unconfirmed",
            "provider": "error",
            "summary": f"{tool_name} 工具调用异常：{exc}",
            "warnings": [f"{tool_name} 调用异常，{tool_name}信息未确认。"],
            "raw": {},
        }


def search_for_route(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict,
) -> dict:
    location = _route_location(route.manual_tags or {}, analysis.analysis_json or {})
    activity_goal = context_state.get("activity_goal")
    query_parts = [route.name]
    if location and location != "unknown":
        query_parts.append(location)
    query_parts.append(activity_goal if isinstance(activity_goal, str) else "徒步")
    query_parts.extend(["近期", "路况"])
    return search_evidence_json(
        SearchRequest(
            query=" ".join(query_parts),
            route_name=route.name,
            max_results=5,
        )
    )


def summarize_web_evidence(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict,
    web_evidence: dict,
    llm_provider: AgentLLMProvider | None,
) -> dict:
    sources = web_evidence.get("sources")
    if not isinstance(sources, list) or not sources:
        return web_evidence

    contacts = emergency_contacts_from_sources(sources)
    web_evidence["emergency_contacts"] = contacts
    if llm_provider is None:
        return web_evidence

    try:
        result = llm_provider.generate_response(
            ResponseGenerationInput(
                kind="web_evidence_summary",
                context_state=context_state or {},
                candidate_count=1,
                candidate_routes=[
                    {
                        "route_name": route.name,
                        "distance_km": analysis.distance_km,
                        "elevation_gain_m": analysis.elevation_gain_m,
                        "web_evidence": {
                            "status": web_evidence.get("status"),
                            "query": web_evidence.get("query"),
                            "sources": [
                                {
                                    "title": source.get("title"),
                                    "url": source.get("url"),
                                    "content": source.get("content"),
                                }
                                for source in sources[:5]
                                if isinstance(source, dict)
                            ],
                            "emergency_contacts": contacts,
                        },
                    }
                ],
            )
        )
        if result.content.strip():
            web_evidence["ai_summary"] = result.content.strip()
            web_evidence["summary"] = result.content.strip()
            web_evidence["summary_provider"] = result.provider
    except Exception as exc:
        logger.exception("Web evidence LLM summary failed")
        warnings = web_evidence.setdefault("warnings", [])
        if isinstance(warnings, list):
            warnings.append(f"AI 摘要生成失败：{exc}")
    return web_evidence


def emergency_contacts_from_sources(sources: list[dict]) -> list[dict]:
    contacts: list[dict] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        haystack = " ".join(
            str(source.get(field) or "")
            for field in ("title", "content", "url")
        )
        for match in PHONE_PATTERN.findall(haystack):
            phone = re.sub(r"[\s-]+", "", match)
            if phone in seen:
                continue
            seen.add(phone)
            contacts.append(
                {
                    "phone": phone,
                    "label": phone_label(phone),
                    "source_url": source.get("url"),
                    "source_title": source.get("title"),
                }
            )
    return contacts


def phone_label(phone: str) -> str:
    return {
        "110": "公安报警",
        "119": "消防救援",
        "120": "医疗急救",
        "12122": "高速公路报警救援",
        "12345": "政务服务热线",
        "12315": "消费者投诉举报",
    }.get(phone, "公开来源电话")


def enrich_weather_for_route(weather: dict, analysis: RouteAnalysisSnapshot) -> dict:
    weather = dict(weather or {})
    current = weather.get("current") if isinstance(weather.get("current"), dict) else None
    daily = weather.get("daily_forecast") if isinstance(weather.get("daily_forecast"), list) else []
    if current:
        temp = _float_or_none(current.get("temp"))
        wind_kmh = _wind_scale_to_kmh(current.get("wind_scale"))
        feels_like = _float_or_none(current.get("feels_like"))
        weather["outdoor_indices"] = {
            "feels_like_c": round(feels_like if feels_like is not None else _apparent_temperature(temp, wind_kmh), 1)
            if temp is not None
            else None,
            "wind_chill_c": _wind_chill(temp, wind_kmh),
            "wind_speed_estimated_kmh": wind_kmh,
            "uv_index": _first_uv_index(daily),
            "uv_level": _uv_level(_first_uv_index(daily)),
            "comfort_level": _comfort_level(temp, wind_kmh),
        }

    high_elevation = _float_or_none(getattr(analysis, "elevation_max_m", None))
    min_elevation = _float_or_none(getattr(analysis, "elevation_min_m", None))
    if current and high_elevation is not None:
        base_temp = _float_or_none(current.get("temp"))
        elevation_delta = max(0.0, high_elevation - (min_elevation or 0.0))
        temp_drop = elevation_delta * 0.006
        estimated_temp = round(base_temp - temp_drop, 1) if base_temp is not None else None
        weather["highest_point_weather_estimate"] = {
            "elevation_m": round(high_elevation),
            "estimated_temp_c": estimated_temp,
            "lapse_rate_c_per_100m": 0.6,
            "basis": "按海拔每升高 100 米气温约下降 0.6°C 估算，非实测值。",
        }
    return weather


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _wind_scale_to_kmh(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None
    scale = sum(numbers) / len(numbers)
    beaufort_kmh = {
        0: 1,
        1: 4,
        2: 9,
        3: 16,
        4: 24,
        5: 35,
        6: 45,
        7: 56,
        8: 68,
        9: 81,
        10: 96,
        11: 112,
        12: 125,
    }
    low = max(0, min(12, int(scale)))
    high = max(0, min(12, int(round(scale))))
    return round((beaufort_kmh[low] + beaufort_kmh[high]) / 2, 1)


def _apparent_temperature(temp_c: float | None, wind_kmh: float | None) -> float | None:
    if temp_c is None:
        return None
    chill = _wind_chill(temp_c, wind_kmh)
    return chill if chill is not None else temp_c


def _wind_chill(temp_c: float | None, wind_kmh: float | None) -> float | None:
    if temp_c is None or wind_kmh is None or temp_c > 10 or wind_kmh <= 4.8:
        return None
    value = 13.12 + 0.6215 * temp_c - 11.37 * (wind_kmh ** 0.16) + 0.3965 * temp_c * (wind_kmh ** 0.16)
    return round(value, 1)


def _first_uv_index(daily: list) -> int | None:
    for item in daily:
        if isinstance(item, dict):
            value = _float_or_none(item.get("uv_index"))
            if value is not None:
                return int(value)
    return None


def _uv_level(value: int | None) -> str:
    if value is None:
        return "未确认"
    if value <= 2:
        return "低"
    if value <= 5:
        return "中等"
    if value <= 7:
        return "高"
    if value <= 10:
        return "很高"
    return "极高"


def _comfort_level(temp_c: float | None, wind_kmh: float | None) -> str:
    if temp_c is None:
        return "未确认"
    if temp_c <= 0:
        return "寒冷"
    if temp_c <= 8:
        return "偏冷"
    if temp_c <= 22:
        return "适中"
    if temp_c <= 28:
        return "偏热"
    if wind_kmh and wind_kmh >= 40:
        return "风大，体感不稳定"
    return "炎热"


def weather_for_route(route: RouteAsset, analysis: RouteAnalysisSnapshot) -> dict:
    center = analysis.center_point or {}
    lon = center.get("lon")
    lat = center.get("lat")
    if not isinstance(lon, int | float) or not isinstance(lat, int | float):
        return {
            "status": "unconfirmed",
            "provider": "mock",
            "summary": "缺少线路中心点，天气未确认。",
            "warnings": [],
            "raw": {},
        }
    return weather_evidence_json(
        WeatherRequest(
            lon=float(lon),
            lat=float(lat),
            location_name=_route_location(route.manual_tags or {}, analysis.analysis_json or {}),
            days=3,
        )
    )


def transport_for_route(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict,
) -> dict:
    center = analysis.center_point or {}
    lon = center.get("lon")
    lat = center.get("lat")
    destination_coordinate = None
    if isinstance(lon, int | float) and isinstance(lat, int | float):
        destination_coordinate = {"lon": float(lon), "lat": float(lat)}

    return transport_evidence_json(
        TransportRequest(
            origin_name=geo_raw_text(context_state.get("departure_area")),
            destination_name=_route_location(route.manual_tags or {}, analysis.analysis_json or {}),
            destination_coordinate=destination_coordinate,
            preferred_mode=preferred_transport_mode(context_state),
            route_distance_km=analysis.distance_km,
            destination_city=destination_city(analysis.analysis_json or {}),
            cross_city_hint=cross_city_hint(context_state, analysis.analysis_json or {}),
        )
    )


def preferred_transport_mode(context_state: dict) -> str | None:
    transport_hint = context_state.get("transport_hint")
    if transport_hint in {
        "self_drive",
        "public_transport",
        "bus",
        "rail_plus_car",
        "flight_plus_car",
    }:
        return transport_hint
    return None


def destination_city(analysis_json: dict) -> str | None:
    location = analysis_json.get("location")
    if isinstance(location, dict) and isinstance(location.get("city"), str):
        return location["city"]
    return None


def cross_city_hint(context_state: dict, analysis_json: dict) -> bool:
    departure = geo_raw_text(context_state.get("departure_area"))
    city = destination_city(analysis_json)
    if isinstance(departure, str) and isinstance(city, str):
        return departure not in city
    return False
