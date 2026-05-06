from __future__ import annotations

from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings

TransportStatus = Literal["mocked", "confirmed", "unconfirmed", "unavailable"]
TransportMode = Literal[
    "self_drive",
    "public_transport",
    "bus",
    "rail_plus_car",
    "flight_plus_car",
]
Feasibility = Literal["recommended", "available", "limited", "unavailable"]

AMAP_BASE_URL = "https://restapi.amap.com"


class Coordinate(BaseModel):
    lon: float
    lat: float


class TransportRequest(BaseModel):
    origin_name: str | None = None
    destination_name: str | None = None
    origin_coordinate: Coordinate | None = None
    destination_coordinate: Coordinate | None = None
    preferred_mode: TransportMode | None = None
    route_distance_km: float | None = None
    destination_city: str | None = None
    cross_city_hint: bool = False


class TransportStep(BaseModel):
    type: str
    line_name: str | None = None
    instruction: str


class TransportPlan(BaseModel):
    mode: TransportMode
    feasibility: Feasibility
    duration_minutes: int | None = None
    distance_km: float | None = None
    driving_distance_km: float | None = None
    walking_distance_m: int | None = None
    transfer_count: int | None = None
    tolls_cny: float | None = None
    railway_lines: list[str] = Field(default_factory=list)
    bus_lines: list[str] = Field(default_factory=list)
    steps: list[TransportStep] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class TransportEvidence(BaseModel):
    status: TransportStatus
    provider: str
    preferred_mode: TransportMode | None = None
    recommended_mode: TransportMode | None = None
    preference_matched: bool | None = None
    summary: str
    plans: list[TransportPlan] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


def get_transport_evidence(payload: TransportRequest) -> TransportEvidence:
    settings = get_settings()
    preferred_mode: TransportMode = payload.preferred_mode or "self_drive"

    if settings.use_mock_amap:
        return _mock_transport(payload, preferred_mode)

    if not settings.amap_web_service_key:
        return TransportEvidence(
            status="unconfirmed",
            provider="amap",
            preferred_mode=preferred_mode,
            summary="未配置高德 WebService Key，交通信息未确认。",
        )

    return _amap_transport(payload, preferred_mode, settings.amap_web_service_key)


def transport_evidence_json(payload: TransportRequest) -> dict[str, Any]:
    return get_transport_evidence(payload).model_dump()


def _amap_transport(
    payload: TransportRequest,
    preferred_mode: TransportMode,
    api_key: str,
) -> TransportEvidence:
    raw: dict[str, Any] = {}
    try:
        with httpx.Client(timeout=10.0, trust_env=False) as client:
            origin = payload.origin_coordinate or _geocode_first(
                client,
                payload.origin_name,
                api_key,
                raw,
            )
            destination = payload.destination_coordinate
            if origin is None or destination is None:
                return TransportEvidence(
                    status="unconfirmed",
                    provider="amap",
                    preferred_mode=preferred_mode,
                    summary="缺少可用的出发地或目的地坐标，无法确认高德交通方案。",
                    raw=raw,
                )

            plans: list[TransportPlan] = []
            if preferred_mode == "self_drive":
                plans.append(_amap_driving_plan(client, origin, destination, api_key, raw))
                plans.extend(_try_transit_plans(client, payload, origin, destination, api_key, raw))
            elif preferred_mode in {"public_transport", "bus", "rail_plus_car"}:
                plans.extend(_try_transit_plans(client, payload, origin, destination, api_key, raw))
                if not plans or payload.cross_city_hint:
                    plans.insert(0, _amap_driving_plan(client, origin, destination, api_key, raw))
            elif preferred_mode == "flight_plus_car":
                plans.append(_flight_unavailable_plan())
                plans.append(_amap_driving_plan(client, origin, destination, api_key, raw))
    except (httpx.HTTPError, ToolRequestError) as exc:
        return TransportEvidence(
            status="unconfirmed",
            provider="amap",
            preferred_mode=preferred_mode,
            summary=f"高德交通调用失败，交通信息未确认：{exc}",
            raw=raw,
        )

    plans = [plan for plan in plans if plan.feasibility != "unavailable" or preferred_mode == "flight_plus_car"]
    if not plans:
        return TransportEvidence(
            status="unconfirmed",
            provider="amap",
            preferred_mode=preferred_mode,
            summary="高德未返回可用交通方案，交通信息未确认。",
            raw=raw,
        )

    recommended_mode = _recommended_mode(preferred_mode, payload, plans)
    _mark_recommended_plan(plans, recommended_mode)
    return TransportEvidence(
        status="confirmed",
        provider="amap",
        preferred_mode=preferred_mode,
        recommended_mode=recommended_mode,
        preference_matched=recommended_mode == preferred_mode,
        summary=_transport_summary(preferred_mode, recommended_mode, plans),
        plans=plans,
        raw=raw,
    )


def _geocode_first(
    client: httpx.Client,
    address: str | None,
    api_key: str,
    raw: dict[str, Any],
) -> Coordinate | None:
    if not address:
        return None
    data = _amap_get(
        client,
        f"{AMAP_BASE_URL}/v3/geocode/geo",
        {"address": address, "key": api_key},
    )
    raw["geocode_origin"] = data
    geocodes = data.get("geocodes")
    if not isinstance(geocodes, list) or not geocodes:
        return None
    location = str((geocodes[0] or {}).get("location") or "")
    parts = location.split(",")
    if len(parts) != 2:
        return None
    lon = _float_or_none(parts[0])
    lat = _float_or_none(parts[1])
    if lon is None or lat is None:
        return None
    return Coordinate(lon=lon, lat=lat)


def _amap_driving_plan(
    client: httpx.Client,
    origin: Coordinate,
    destination: Coordinate,
    api_key: str,
    raw: dict[str, Any],
) -> TransportPlan:
    data = _amap_get(
        client,
        f"{AMAP_BASE_URL}/v3/direction/driving",
        {
            "origin": _coord(origin),
            "destination": _coord(destination),
            "extensions": "base",
            "key": api_key,
        },
    )
    raw["driving"] = data
    paths = ((data.get("route") or {}).get("paths") or [])
    if not paths:
        raise ToolRequestError("高德驾车路线为空")
    path = paths[0]
    distance_m = _float_or_none(path.get("distance"))
    duration_s = _float_or_none(path.get("duration"))
    steps = path.get("steps") if isinstance(path.get("steps"), list) else []
    return TransportPlan(
        mode="self_drive",
        feasibility="available",
        duration_minutes=_minutes(duration_s),
        distance_km=round(distance_m / 1000, 1) if distance_m is not None else None,
        driving_distance_km=round(distance_m / 1000, 1) if distance_m is not None else None,
        tolls_cny=_float_or_none(path.get("tolls")),
        steps=[
            TransportStep(
                type="drive",
                instruction=str(step.get("instruction") or "").strip(),
            )
            for step in steps[:6]
            if isinstance(step, dict) and str(step.get("instruction") or "").strip()
        ],
        risk_notes=["停车点、山路路况和返程拥堵仍需出发前复核。"],
    )


def _try_transit_plans(
    client: httpx.Client,
    payload: TransportRequest,
    origin: Coordinate,
    destination: Coordinate,
    api_key: str,
    raw: dict[str, Any],
) -> list[TransportPlan]:
    city = payload.origin_name or payload.destination_city
    if not city:
        return []
    params = {
        "origin": _coord(origin),
        "destination": _coord(destination),
        "city": city,
        "strategy": "0",
        "key": api_key,
    }
    if payload.destination_city and payload.cross_city_hint:
        params["cityd"] = payload.destination_city
    try:
        data = _amap_get(
            client,
            f"{AMAP_BASE_URL}/v3/direction/transit/integrated",
            params,
        )
    except ToolRequestError:
        return []
    raw["transit"] = data
    transits = ((data.get("route") or {}).get("transits") or [])
    if not isinstance(transits, list):
        return []
    return [_parse_transit_plan(item) for item in transits[:3] if isinstance(item, dict)]


def _parse_transit_plan(item: dict[str, Any]) -> TransportPlan:
    duration_s = _float_or_none(item.get("duration"))
    walking_distance = _int_or_none(item.get("walking_distance"))
    segments = item.get("segments") if isinstance(item.get("segments"), list) else []
    steps: list[TransportStep] = []
    bus_lines: list[str] = []
    railway_lines: list[str] = []

    for segment in segments:
        if not isinstance(segment, dict):
            continue
        bus = segment.get("bus")
        if isinstance(bus, dict):
            for line in bus.get("buslines") or []:
                if not isinstance(line, dict):
                    continue
                name = str(line.get("name") or "").strip()
                line_type = str(line.get("type") or "").strip()
                if not name:
                    continue
                step_type = "subway" if "地铁" in name or "地铁" in line_type else "bus"
                bus_lines.append(name)
                steps.append(TransportStep(type=step_type, line_name=name, instruction=f"乘坐{name}"))
        railway = segment.get("railway")
        if isinstance(railway, dict):
            name = str(railway.get("name") or railway.get("trip") or "").strip()
            if name:
                railway_lines.append(name)
                steps.append(TransportStep(type="railway", line_name=name, instruction=f"乘坐{name}"))
        walking = segment.get("walking")
        if isinstance(walking, dict) and _float_or_none(walking.get("distance")):
            steps.append(TransportStep(type="walk", instruction="步行接驳"))

    has_rail = bool(railway_lines)
    return TransportPlan(
        mode="public_transport",
        feasibility="available",
        duration_minutes=_minutes(duration_s),
        walking_distance_m=walking_distance,
        transfer_count=max(len([step for step in steps if step.type in {"bus", "subway", "railway"}]) - 1, 0),
        railway_lines=_unique(railway_lines),
        bus_lines=_unique(bus_lines),
        steps=steps[:8],
        risk_notes=["班次、末班车、景区接驳和返程能力需出发前复核。"],
    )


def _flight_unavailable_plan() -> TransportPlan:
    return TransportPlan(
        mode="flight_plus_car",
        feasibility="limited",
        risk_notes=["航班信息未接入本轮真实工具，不能确认航班班次和价格。"],
        steps=[
            TransportStep(
                type="flight",
                instruction="航班段未接入真实查询，建议后续接入航班 API 或人工确认。",
            )
        ],
    )


def _amap_get(
    client: httpx.Client,
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    response = client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if str(data.get("status")) != "1":
        raise ToolRequestError(f"{data.get('info') or '高德返回失败'}({data.get('infocode')})")
    return data


def _recommended_mode(
    preferred_mode: TransportMode,
    payload: TransportRequest,
    plans: list[TransportPlan],
) -> TransportMode:
    if preferred_mode == "bus" and (
        payload.cross_city_hint or any(plan.railway_lines for plan in plans)
    ):
        return "rail_plus_car"
    if any(plan.mode == preferred_mode for plan in plans):
        return preferred_mode
    if plans:
        return plans[0].mode
    return preferred_mode


def _mark_recommended_plan(plans: list[TransportPlan], mode: TransportMode) -> None:
    if mode == "rail_plus_car":
        for plan in plans:
            if plan.railway_lines:
                plan.mode = "rail_plus_car"
                plan.feasibility = "recommended"
                return
    for plan in plans:
        if plan.mode == mode:
            plan.feasibility = "recommended"
            return


def _transport_summary(
    preferred_mode: TransportMode,
    recommended_mode: TransportMode,
    plans: list[TransportPlan],
) -> str:
    first = next((plan for plan in plans if plan.mode == recommended_mode), plans[0])
    duration = f"，约 {first.duration_minutes} 分钟" if first.duration_minutes else ""
    distance = f"，约 {first.distance_km:g} km" if first.distance_km else ""
    prefix = "高德已返回交通方案"
    if preferred_mode != recommended_mode:
        prefix += f"；你偏好{_mode_label(preferred_mode)}，但当前更建议优先看{_mode_label(recommended_mode)}"
    else:
        prefix += f"；{_mode_label(recommended_mode)}与偏好一致"
    return f"{prefix}{duration}{distance}。实际班次、封路、停车和返程仍需出发前复核。"


def _mock_transport(
    payload: TransportRequest,
    preferred_mode: TransportMode,
) -> TransportEvidence:
    if _should_recommend_rail_plus_car(payload, preferred_mode):
        plans = [_rail_plus_car_plan(), _bus_limited_plan(), _self_drive_plan(payload)]
        return TransportEvidence(
            status="mocked",
            provider="mock",
            preferred_mode=preferred_mode,
            recommended_mode="rail_plus_car",
            preference_matched=False,
            summary="你倾向大巴，但该候选路线存在跨市或长距离因素；mock 评估中高铁/城际 + 短途打车或租车更现实。",
            plans=plans,
        )

    if preferred_mode == "public_transport":
        plan = _public_transport_plan()
        return TransportEvidence(
            status="mocked",
            provider="mock",
            preferred_mode=preferred_mode,
            recommended_mode="public_transport",
            preference_matched=True,
            summary="公共交通为 mock 方案，包含地铁/轨道和公交接驳，实际班次需出发前核实。",
            plans=[plan, _self_drive_plan(payload)],
        )

    if preferred_mode == "bus":
        plan = _bus_available_plan()
        return TransportEvidence(
            status="mocked",
            provider="mock",
            preferred_mode=preferred_mode,
            recommended_mode="bus",
            preference_matched=True,
            summary="大巴为 mock 方案，班次和末班车需要出发前核实。",
            plans=[plan, _public_transport_plan(), _self_drive_plan(payload)],
        )

    plan = _self_drive_plan(payload)
    return TransportEvidence(
        status="mocked",
        provider="mock",
        preferred_mode=preferred_mode,
        recommended_mode="self_drive",
        preference_matched=preferred_mode == "self_drive",
        summary="自驾交通为 mock 方案，真实耗时和路况需要用地图确认。",
        plans=[plan, _public_transport_plan()],
    )


def _should_recommend_rail_plus_car(
    payload: TransportRequest,
    preferred_mode: TransportMode,
) -> bool:
    if preferred_mode != "bus":
        return False
    if payload.cross_city_hint:
        return True
    return bool(payload.route_distance_km and payload.route_distance_km >= 160)


def _self_drive_plan(payload: TransportRequest) -> TransportPlan:
    distance = payload.route_distance_km or 120
    driving_distance = max(distance * 1.25, 30)
    duration = int(driving_distance / 55 * 60)
    return TransportPlan(
        mode="self_drive",
        feasibility="available",
        duration_minutes=max(duration, 45),
        distance_km=round(driving_distance, 1),
        driving_distance_km=round(driving_distance, 1),
        tolls_cny=round(driving_distance * 0.35, 1),
        steps=[TransportStep(type="drive", instruction="从出发地自驾至线路起点，真实路线和路况需要用高德确认。")],
        risk_notes=["山区道路、停车点和返程拥堵未确认。"],
    )


def _public_transport_plan() -> TransportPlan:
    return TransportPlan(
        mode="public_transport",
        feasibility="available",
        duration_minutes=180,
        walking_distance_m=1200,
        transfer_count=2,
        railway_lines=["地铁2号线", "城际铁路"],
        bus_lines=["景区接驳车"],
        steps=[
            TransportStep(type="subway", line_name="地铁2号线", instruction="乘坐地铁2号线到换乘站。"),
            TransportStep(type="railway", line_name="城际铁路", instruction="换乘城际铁路靠近目的地城市。"),
            TransportStep(type="bus", line_name="景区接驳车", instruction="换乘公交或景区接驳到线路起点附近。"),
        ],
        risk_notes=["班次、末班车和景区接驳是否运营未确认。"],
    )


def _bus_available_plan() -> TransportPlan:
    return TransportPlan(
        mode="bus",
        feasibility="available",
        duration_minutes=240,
        transfer_count=1,
        walking_distance_m=900,
        bus_lines=["城际大巴", "景区接驳车"],
        steps=[
            TransportStep(type="bus", line_name="城际大巴", instruction="乘坐城际大巴到目的地客运站。"),
            TransportStep(type="bus", line_name="景区接驳车", instruction="换乘接驳车到线路起点附近。"),
        ],
        risk_notes=["大巴班次和返程末班车未确认。"],
    )


def _bus_limited_plan() -> TransportPlan:
    plan = _bus_available_plan()
    plan.feasibility = "limited"
    plan.duration_minutes = 420
    plan.risk_notes = ["跨市大巴耗时长，班次和末班车风险较高。"]
    return plan


def _rail_plus_car_plan() -> TransportPlan:
    return TransportPlan(
        mode="rail_plus_car",
        feasibility="recommended",
        duration_minutes=210,
        driving_distance_km=35,
        walking_distance_m=600,
        transfer_count=1,
        railway_lines=["高铁/城际"],
        steps=[
            TransportStep(type="railway", line_name="高铁/城际", instruction="先乘坐高铁或城际到目的地附近城市。"),
            TransportStep(type="drive", instruction="末段打车、租车或包车到线路起点。"),
        ],
        risk_notes=["末段接驳车辆、返程车源和费用未确认。"],
    )


def _coord(coordinate: Coordinate) -> str:
    return f"{coordinate.lon:.6f},{coordinate.lat:.6f}"


def _minutes(seconds: float | None) -> int | None:
    if seconds is None:
        return None
    return max(int(round(seconds / 60)), 1)


def _mode_label(mode: TransportMode) -> str:
    return {
        "self_drive": "自驾",
        "public_transport": "公共交通",
        "bus": "大巴",
        "rail_plus_car": "高铁/城际 + 末段接驳",
        "flight_plus_car": "飞机 + 末段接驳",
    }[mode]


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


class ToolRequestError(Exception):
    pass
