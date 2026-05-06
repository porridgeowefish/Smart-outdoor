from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any

REST_WINDOW_SECONDS = 15 * 60
REST_DISPLACEMENT_KM = 0.1


class TrackParseError(Exception):
    def __str__(self) -> str:
        return "TRACK_PARSE_FAILED"


@dataclass(frozen=True)
class TrackPoint:
    lon: float
    lat: float
    ele: float | None = None
    time: datetime | None = None


@dataclass(frozen=True)
class TrackAnalysis:
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    elevation_min_m: float | None
    elevation_max_m: float | None
    climb_ratio: float | None
    steep_ratio: float | None
    start_point: dict[str, float]
    end_point: dict[str, float]
    bounds: dict[str, float]
    center_point: dict[str, float]
    track_geojson: dict[str, Any]
    analysis_json: dict[str, Any]
    moving_time_seconds: int | None = None
    timed_points: list[TrackPoint] | None = None


def parse_track(content: bytes, file_type: str) -> TrackAnalysis:
    try:
        if file_type == "gpx":
            points = _parse_gpx(content)
        elif file_type == "geojson":
            points = _parse_geojson(content)
        elif file_type == "kml":
            points = _parse_kml(content)
        else:
            raise TrackParseError
        return _analyze_points(_densify_points(points))
    except TrackParseError:
        raise
    except Exception as exc:
        raise TrackParseError from exc


def _parse_gpx(content: bytes) -> list[TrackPoint]:
    root = ET.fromstring(content)
    points: list[TrackPoint] = []
    for element in root.iter():
        if _local_name(element.tag) != "trkpt":
            continue
        lat = float(element.attrib["lat"])
        lon = float(element.attrib["lon"])
        ele = None
        point_time = None
        for child in element:
            if _local_name(child.tag) == "ele" and child.text:
                ele = float(child.text)
            if _local_name(child.tag) == "time" and child.text:
                point_time = _parse_time(child.text)
        points.append(TrackPoint(lon=lon, lat=lat, ele=ele, time=point_time))
    return points


def _parse_geojson(content: bytes) -> list[TrackPoint]:
    data = json.loads(content.decode("utf-8"))
    geometry = data.get("geometry") if data.get("type") == "Feature" else data
    if geometry.get("type") == "FeatureCollection":
        points: list[TrackPoint] = []
        for feature in geometry.get("features") or []:
            points.extend(_geojson_geometry_to_points(feature.get("geometry") or {}))
        return _deduplicate_adjacent_points(points)
    return _deduplicate_adjacent_points(_geojson_geometry_to_points(geometry))


def _geojson_geometry_to_points(geometry: dict) -> list[TrackPoint]:
    if geometry.get("type") == "LineString":
        coordinates = geometry.get("coordinates") or []
        times = _geojson_times(geometry)
        return [
            _coordinate_to_point(item, times[index] if index < len(times) else None)
            for index, item in enumerate(coordinates)
        ]
    if geometry.get("type") == "MultiLineString":
        points: list[TrackPoint] = []
        for line in geometry.get("coordinates") or []:
            points.extend(_coordinate_to_point(item) for item in line)
        return points
    raise TrackParseError


def _parse_kml(content: bytes) -> list[TrackPoint]:
    root = ET.fromstring(content)
    gx_points = _extract_gx_track_points(root)
    line_string_points = _extract_line_string_coords(root)

    points = _choose_kml_track_points(line_string_points, gx_points)
    if not points:
        raise TrackParseError

    return _clean_kml_points(_deduplicate_adjacent_points(points))


def _extract_gx_track_points(root: ET.Element) -> list[TrackPoint]:
    points: list[TrackPoint] = []
    for track in root.iter():
        if _local_name(track.tag) != "Track":
            continue

        coords: list[str] = []
        times: list[datetime | None] = []
        for element in track.iter():
            local_name = _local_name(element.tag)
            if local_name == "when" and element.text:
                times.append(_parse_time(element.text))
            elif local_name == "coord" and element.text:
                coords.append(element.text)

        for index, raw_coord in enumerate(coords):
            parts = raw_coord.split()
            if len(parts) < 2:
                continue
            ele = float(parts[2]) if len(parts) >= 3 and parts[2] else None
            point_time = times[index] if index < len(times) else None
            points.append(
                TrackPoint(
                    lon=float(parts[0]),
                    lat=float(parts[1]),
                    ele=ele,
                    time=point_time,
                )
            )
    return points


def _extract_line_string_coords(root: ET.Element) -> list[TrackPoint]:
    points: list[TrackPoint] = []
    for element in root.iter():
        if _local_name(element.tag) != "LineString":
            continue
        for child in element:
            if _local_name(child.tag) != "coordinates" or not child.text:
                continue
            for raw_coordinate in child.text.strip().split():
                parts = raw_coordinate.split(",")
                if len(parts) < 2:
                    continue
                ele = float(parts[2]) if len(parts) >= 3 and parts[2] else None
                points.append(TrackPoint(lon=float(parts[0]), lat=float(parts[1]), ele=ele))
    return points


def _choose_kml_track_points(
    coordinate_points: list[TrackPoint], gx_points: list[TrackPoint]
) -> list[TrackPoint]:
    if not coordinate_points:
        return gx_points
    if not gx_points:
        return coordinate_points
    return gx_points if len(gx_points) >= len(coordinate_points) else coordinate_points


def _coordinate_to_point(
    coordinate: list[float], point_time: datetime | None = None
) -> TrackPoint:
    if len(coordinate) < 2:
        raise TrackParseError
    ele = float(coordinate[2]) if len(coordinate) >= 3 else None
    return TrackPoint(
        lon=float(coordinate[0]), lat=float(coordinate[1]), ele=ele, time=point_time
    )


def _clean_kml_points(points: list[TrackPoint]) -> list[TrackPoint]:
    non_zero_elevations = [point.ele for point in points if point.ele not in (None, 0)]
    if not non_zero_elevations:
        return points
    return [
        TrackPoint(
            lon=point.lon,
            lat=point.lat,
            ele=None if point.ele == 0 else point.ele,
            time=point.time,
        )
        for point in points
    ]


def _deduplicate_adjacent_points(points: list[TrackPoint]) -> list[TrackPoint]:
    deduplicated: list[TrackPoint] = []
    for point in points:
        if deduplicated and deduplicated[-1] == point:
            continue
        deduplicated.append(point)
    return deduplicated


def _densify_points(points: list[TrackPoint], max_spacing_km: float = 0.01) -> list[TrackPoint]:
    if len(points) < 2:
        return points

    densified: list[TrackPoint] = [points[0]]
    for previous, current in zip(points, points[1:]):
        segment_km = _haversine_km(previous, current)
        steps = max(1, math.ceil(segment_km / max_spacing_km))
        for step in range(1, steps + 1):
            ratio = step / steps
            densified.append(
                TrackPoint(
                    lon=_interpolate(previous.lon, current.lon, ratio),
                    lat=_interpolate(previous.lat, current.lat, ratio),
                    ele=_interpolate_optional(previous.ele, current.ele, ratio),
                    time=_interpolate_time(previous.time, current.time, ratio),
                )
            )
    return _deduplicate_adjacent_points(densified)


def _analyze_points(points: list[TrackPoint]) -> TrackAnalysis:
    if len(points) < 2:
        raise TrackParseError

    distance_km = 0.0
    elevation_gain_m = 0.0
    elevation_loss_m = 0.0
    elevations = [point.ele for point in points if point.ele is not None]

    for previous, current in zip(points, points[1:]):
        distance_km += _haversine_km(previous, current)
        if previous.ele is None or current.ele is None:
            continue
        diff = current.ele - previous.ele
        if diff > 0:
            elevation_gain_m += diff
        elif diff < 0:
            elevation_loss_m += abs(diff)

    lons = [point.lon for point in points]
    lats = [point.lat for point in points]
    bounds = {
        "min_lon": min(lons),
        "min_lat": min(lats),
        "max_lon": max(lons),
        "max_lat": max(lats),
    }
    center_point = {
        "lon": (bounds["min_lon"] + bounds["max_lon"]) / 2,
        "lat": (bounds["min_lat"] + bounds["max_lat"]) / 2,
    }

    climb_ratio = elevation_gain_m / distance_km if distance_km > 0 else None
    elapsed_time_seconds = _elapsed_time_seconds(points)
    rest_time_seconds = _rest_time_seconds(points)
    moving_time_seconds = (
        max(0, elapsed_time_seconds - rest_time_seconds)
        if elapsed_time_seconds is not None
        else None
    )
    track_geojson = {
        "type": "LineString",
        "coordinates": [_point_to_coordinate(point) for point in points],
    }

    return TrackAnalysis(
        distance_km=round(distance_km, 4),
        elevation_gain_m=round(elevation_gain_m, 2),
        elevation_loss_m=round(elevation_loss_m, 2),
        elevation_min_m=min(elevations) if elevations else None,
        elevation_max_m=max(elevations) if elevations else None,
        climb_ratio=round(climb_ratio, 2) if climb_ratio is not None else None,
        steep_ratio=None,
        start_point=_point_to_dict(points[0]),
        end_point=_point_to_dict(points[-1]),
        bounds=bounds,
        center_point=center_point,
        track_geojson=track_geojson,
        analysis_json={
            "point_count": len(points),
            "has_time_data": moving_time_seconds is not None,
            "has_elevation_data": bool(elevations),
            "elapsed_time_seconds": elapsed_time_seconds,
            "rest_time_seconds": rest_time_seconds,
            "moving_time_seconds": moving_time_seconds,
        },
        moving_time_seconds=moving_time_seconds,
        timed_points=points,
    )


def _point_to_coordinate(point: TrackPoint) -> list[float]:
    if point.ele is None:
        return [point.lon, point.lat]
    return [point.lon, point.lat, point.ele]


def _point_to_dict(point: TrackPoint) -> dict[str, float]:
    result = {"lon": point.lon, "lat": point.lat}
    if point.ele is not None:
        result["ele"] = point.ele
    return result


def _points_distance_km(points: list[TrackPoint]) -> float:
    return sum(_haversine_km(previous, current) for previous, current in zip(points, points[1:]))


def _haversine_km(start: TrackPoint, end: TrackPoint) -> float:
    earth_radius_km = 6371.0088
    lat1 = math.radians(start.lat)
    lat2 = math.radians(end.lat)
    d_lat = math.radians(end.lat - start.lat)
    d_lon = math.radians(end.lon - start.lon)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def _interpolate(start: float, end: float, ratio: float) -> float:
    return start + (end - start) * ratio


def _interpolate_optional(
    start: float | None, end: float | None, ratio: float
) -> float | None:
    if start is None or end is None:
        return None
    return _interpolate(start, end, ratio)


def _interpolate_time(
    start: datetime | None, end: datetime | None, ratio: float
) -> datetime | None:
    if start is None or end is None:
        return None
    return start + (end - start) * ratio


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _geojson_times(geometry: dict) -> list[datetime | None]:
    properties = geometry.get("properties") if isinstance(geometry.get("properties"), dict) else {}
    raw_times = (
        geometry.get("coordTimes")
        or geometry.get("times")
        or geometry.get("timestamps")
        or properties.get("coordTimes")
        or properties.get("times")
        or properties.get("timestamps")
        or []
    )
    if not isinstance(raw_times, list):
        return []
    return [_parse_time(str(item)) for item in raw_times]


def _elapsed_time_seconds(points: list[TrackPoint]) -> int | None:
    timed = sorted(
        [point.time for point in points if point.time is not None],
        key=lambda value: value,
    )
    if len(timed) < 2:
        return None
    seconds = int((timed[-1] - timed[0]).total_seconds())
    return seconds if seconds > 0 else None


def _rest_time_seconds(points: list[TrackPoint]) -> int:
    timed = sorted(
        [point for point in points if point.time is not None],
        key=lambda point: point.time or datetime.min,
    )
    if len(timed) < 2:
        return 0

    intervals: list[tuple[datetime, datetime]] = []
    end = 1
    for start, start_point in enumerate(timed):
        if end <= start:
            end = start + 1
        while end < len(timed) and _seconds_between(start_point, timed[end]) < REST_WINDOW_SECONDS:
            end += 1
        if end >= len(timed):
            break
        if _haversine_km(start_point, timed[end]) <= REST_DISPLACEMENT_KM:
            intervals.append((start_point.time, timed[end].time))  # type: ignore[arg-type]

    return _merged_interval_seconds(intervals)


def _seconds_between(start: TrackPoint, end: TrackPoint) -> float:
    if start.time is None or end.time is None:
        return 0.0
    return (end.time - start.time).total_seconds()


def _merged_interval_seconds(intervals: list[tuple[datetime, datetime]]) -> int:
    if not intervals:
        return 0

    merged: list[tuple[datetime, datetime]] = []
    for start, end in sorted(intervals, key=lambda item: item[0]):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        if end > previous_end:
            merged[-1] = (previous_start, end)

    return int(sum((end - start).total_seconds() for start, end in merged))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
