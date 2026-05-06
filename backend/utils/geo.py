"""Coordinate conversion helpers for WGS-84 and GCJ-02.

The functions are pure and have no project-level dependencies. They are used
when WGS-84 GPX/KML tracks need to be rendered on AMap/Gaode maps, which use
GCJ-02 coordinates in mainland China.
"""

from __future__ import annotations

import math

_SEMI_MAJOR_AXIS = 6378245.0
_ECCENTRICITY_SQUARED = 0.00669342162296594323
_LON_MIN = 72.004
_LON_MAX = 137.8347
_LAT_MIN = 0.8293
_LAT_MAX = 55.8271


def _is_in_china(lat: float, lon: float) -> bool:
    """Return whether a coordinate is roughly inside mainland China."""
    return _LON_MIN < lon < _LON_MAX and _LAT_MIN < lat < _LAT_MAX


def _transform_lat(lon: float, lat: float) -> float:
    ret = (
        -100.0
        + 2.0 * lon
        + 3.0 * lat
        + 0.2 * lat * lat
        + 0.1 * lon * lat
        + 0.2 * math.sqrt(math.fabs(lon))
    )
    ret += (
        20.0 * math.sin(6.0 * lon * math.pi)
        + 20.0 * math.sin(2.0 * lon * math.pi)
    ) * 2.0 / 3.0
    ret += (
        20.0 * math.sin(lat * math.pi) + 40.0 * math.sin(lat / 3.0 * math.pi)
    ) * 2.0 / 3.0
    ret += (
        160.0 * math.sin(lat / 12.0 * math.pi)
        + 320.0 * math.sin(lat * math.pi / 30.0)
    ) * 2.0 / 3.0
    return ret


def _transform_lon(lon: float, lat: float) -> float:
    ret = (
        300.0
        + lon
        + 2.0 * lat
        + 0.1 * lon * lon
        + 0.1 * lon * lat
        + 0.1 * math.sqrt(math.fabs(lon))
    )
    ret += (
        20.0 * math.sin(6.0 * lon * math.pi)
        + 20.0 * math.sin(2.0 * lon * math.pi)
    ) * 2.0 / 3.0
    ret += (
        20.0 * math.sin(lon * math.pi) + 40.0 * math.sin(lon / 3.0 * math.pi)
    ) * 2.0 / 3.0
    ret += (
        150.0 * math.sin(lon / 12.0 * math.pi)
        + 300.0 * math.sin(lon / 30.0 * math.pi)
    ) * 2.0 / 3.0
    return ret


def _calculate_delta(lon: float, lat: float) -> tuple[float, float]:
    """Calculate GCJ-02 offset relative to WGS-84."""
    if not _is_in_china(lat, lon):
        return 0.0, 0.0

    d_lat = _transform_lat(lon - 105.0, lat - 35.0)
    d_lon = _transform_lon(lon - 105.0, lat - 35.0)

    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1.0 - _ECCENTRICITY_SQUARED * magic * magic
    sqrt_magic = math.sqrt(magic)

    d_lat = (
        d_lat
        * 180.0
        / (
            _SEMI_MAJOR_AXIS
            * (1.0 - _ECCENTRICITY_SQUARED)
            / (magic * sqrt_magic)
            * math.pi
        )
    )
    d_lon = (
        d_lon * 180.0 / (_SEMI_MAJOR_AXIS / sqrt_magic * math.cos(rad_lat) * math.pi)
    )

    return d_lon, d_lat


def wgs84_to_gcj02(lon: float, lat: float) -> tuple[float, float]:
    """Convert a WGS-84 coordinate to GCJ-02."""
    d_lon, d_lat = _calculate_delta(lon, lat)
    return lon + d_lon, lat + d_lat


def gcj02_to_wgs84(lon: float, lat: float) -> tuple[float, float]:
    """Convert a GCJ-02 coordinate to WGS-84 by inverse approximation."""
    if not _is_in_china(lat, lon):
        return lon, lat

    gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
    return lon - (gcj_lon - lon), lat - (gcj_lat - lat)


__all__ = ["wgs84_to_gcj02", "gcj02_to_wgs84"]
