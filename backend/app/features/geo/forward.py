from __future__ import annotations

import json
from typing import Any
from urllib import parse, request

from pydantic import BaseModel

from app.core.config import get_settings

AMAP_FORWARD_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"


class Coordinate(BaseModel):
    lon: float
    lat: float


def forward_geocode(address: str) -> Coordinate | None:
    """Forward-geocode a place name to a Coordinate via Amap /v3/geocode/geo.

    Returns None when mock mode is on, the key is missing, the address is blank,
    the call fails, or Amap reports no result. Mirrors the degrade pattern of
    reverse_geocode_wgs84 so callers can treat None as "unknown, keep going".
    """
    settings = get_settings()
    if settings.use_mock_amap:
        return None
    if not settings.amap_web_service_key:
        return None
    if not address or not address.strip():
        return None

    query = parse.urlencode(
        {
            "key": settings.amap_web_service_key,
            "address": address,
            "output": "JSON",
        }
    )
    url = f"{AMAP_FORWARD_GEOCODE_URL}?{query}"

    try:
        with request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    if payload.get("status") != "1":
        return None

    return _parse_amap_location(payload.get("geocodes"))


def _parse_amap_location(geocodes: Any) -> Coordinate | None:
    if not isinstance(geocodes, list) or not geocodes:
        return None
    location = str((geocodes[0] or {}).get("location") or "")
    parts = location.split(",")
    if len(parts) != 2:
        return None
    try:
        return Coordinate(lon=float(parts[0]), lat=float(parts[1]))
    except (TypeError, ValueError):
        return None
