from __future__ import annotations

import json
import math
from typing import Any
from urllib import parse, request

from app.core.config import get_settings

EARTH_AXIS = 6378245.0
EE = 0.00669342162296594323


def reverse_geocode_wgs84(lon: float, lat: float) -> dict[str, Any] | None:
    settings = get_settings()
    if settings.use_mock_amap:
        return None
    if not settings.amap_web_service_key:
        return None

    gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
    query = parse.urlencode(
        {
            "key": settings.amap_web_service_key,
            "location": f"{gcj_lon:.6f},{gcj_lat:.6f}",
            "extensions": "base",
            "output": "JSON",
            "radius": "1000",
        }
    )
    url = f"{settings.amap_reverse_geocode_url}?{query}"

    try:
        with request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    if payload.get("status") != "1":
        return None

    regeocode = payload.get("regeocode")
    if not isinstance(regeocode, dict):
        return None
    address_component = regeocode.get("addressComponent")
    if not isinstance(address_component, dict):
        return None

    province = _string_or_none(address_component.get("province"))
    city = _string_or_none(address_component.get("city"))
    district = _string_or_none(address_component.get("district"))
    adcode = _string_or_none(address_component.get("adcode"))
    formatted_address = _string_or_none(regeocode.get("formatted_address"))
    display_parts = [item for item in [province, city, district] if item]

    if not display_parts and not formatted_address:
        return None

    return {
        "province": province,
        "city": city,
        "district": district,
        "adcode": adcode,
        "formatted_address": formatted_address,
        "display_name": " · ".join(display_parts) if display_parts else formatted_address,
        "provider": "amap",
        "coordinate_system": "gcj02",
    }


def wgs84_to_gcj02(lon: float, lat: float) -> tuple[float, float]:
    if _outside_china(lon, lat):
        return lon, lat

    d_lat = _transform_lat(lon - 105.0, lat - 35.0)
    d_lon = _transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((EARTH_AXIS * (1 - EE)) / (magic * sqrt_magic) * math.pi)
    d_lon = (d_lon * 180.0) / (EARTH_AXIS / sqrt_magic * math.cos(rad_lat) * math.pi)
    return lon + d_lon, lat + d_lat


def _outside_china(lon: float, lat: float) -> bool:
    return lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271


def _transform_lat(x: float, y: float) -> float:
    result = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y
    result += 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    result += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    result += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    result += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return result


def _transform_lon(x: float, y: float) -> float:
    result = 300.0 + x + 2.0 * y + 0.1 * x * x
    result += 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    result += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    result += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    result += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return result


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
