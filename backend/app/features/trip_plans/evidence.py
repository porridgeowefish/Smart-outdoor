from __future__ import annotations

import logging

from app.features.agent_tools.search import SearchRequest, search_evidence_json
from app.features.agent_tools.transport import TransportRequest, transport_evidence_json
from app.features.agent_tools.weather import WeatherRequest, weather_evidence_json
from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.router import _route_location

logger = logging.getLogger(__name__)


def candidate_evidence(
    route: RouteAsset,
    analysis: RouteAnalysisSnapshot,
    context_state: dict,
) -> dict:
    weather = _safe_call("weather", lambda: weather_for_route(route, analysis))
    transport = _safe_call("transport", lambda: transport_for_route(route, analysis, context_state))
    web_evidence = _safe_call("web_evidence", lambda: search_for_route(route, analysis, context_state))
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
            origin_name=context_state.get("departure_area"),
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
    departure = context_state.get("departure_area")
    city = destination_city(analysis_json)
    if isinstance(departure, str) and isinstance(city, str):
        return departure not in city
    return False
