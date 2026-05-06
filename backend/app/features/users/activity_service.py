from __future__ import annotations

import hashlib
import math
import uuid
from datetime import date
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.features.geo.amap_reverse_geocode import reverse_geocode_wgs84
from app.features.routes.parser import TrackAnalysis, TrackParseError, TrackPoint, parse_track
from app.features.routes.service import UnsupportedRouteFileTypeError, detect_file_type
from app.features.users.model import ActivityTrack, User, UserAbilityProfile

ALGORITHM_VERSION = "ability_v1"


class ActivityTrackParseError(Exception):
    pass


async def upload_activity_track(
    db: Session,
    current_user: User,
    file: UploadFile,
    activity_date: date | None,
    source_type: str = "manual_upload",
) -> tuple[ActivityTrack, UserAbilityProfile]:
    file_type = detect_file_type(file.filename or "")
    content = await file.read()
    try:
        analysis = parse_track(content, file_type)
    except TrackParseError as exc:
        raise ActivityTrackParseError from exc

    track_id = str(uuid.uuid4())
    file_url = _save_activity_file(current_user.id, track_id, file_type, content)
    analysis_json = build_activity_analysis_json(analysis)
    activity = ActivityTrack(
        id=track_id,
        user_id=current_user.id,
        file_url=file_url,
        file_type=file_type,
        file_size_bytes=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        source_type=source_type if source_type else "manual_upload",
        activity_date=activity_date or _activity_date_from_analysis(analysis) or date.today(),
        distance_km=analysis.distance_km,
        elevation_gain_m=analysis.elevation_gain_m,
        elevation_loss_m=analysis.elevation_loss_m,
        elevation_min_m=analysis.elevation_min_m,
        elevation_max_m=analysis.elevation_max_m,
        duration_seconds=analysis.moving_time_seconds,
        moving_time_seconds=analysis.moving_time_seconds,
        track_geojson=analysis.track_geojson,
        analysis_json=analysis_json,
    )
    db.add(activity)
    db.flush()
    profile = recalculate_ability_profile(db, current_user)
    db.commit()
    db.refresh(activity)
    db.refresh(profile)
    return activity, profile


def list_user_activity_tracks(db: Session, user: User) -> list[ActivityTrack]:
    return (
        db.query(ActivityTrack)
        .filter(ActivityTrack.user_id == user.id)
        .order_by(ActivityTrack.activity_date.desc(), ActivityTrack.created_at.desc())
        .all()
    )


def get_user_ability_profile(db: Session, user: User) -> UserAbilityProfile | None:
    return (
        db.query(UserAbilityProfile)
        .filter(UserAbilityProfile.user_id == user.id)
        .first()
    )


def recalculate_ability_profile(db: Session, user: User) -> UserAbilityProfile:
    activities = list_user_activity_tracks(db, user)
    metrics = calculate_profile_metrics(activities)
    profile = get_user_ability_profile(db, user)
    if profile is None:
        profile = UserAbilityProfile(user_id=user.id)
        db.add(profile)

    profile.level = metrics["level"]
    profile.endurance_score = metrics["endurance_score"]
    profile.climb_score = metrics["climb_score"]
    profile.recent_max_distance_km = metrics["recent_max_distance_km"]
    profile.recent_max_elevation_gain_m = metrics["recent_max_elevation_gain_m"]
    profile.activity_count = metrics["activity_count"]
    profile.confidence = metrics["confidence"]
    profile.generated_from_activity_track_ids = [activity.id for activity in activities]
    profile.metrics_json = metrics["metrics_json"]
    profile.message = metrics["message"]
    db.flush()
    return profile


def build_activity_analysis_json(analysis: TrackAnalysis) -> dict:
    effort_km = effort_distance_km(analysis.distance_km, analysis.elevation_gain_m)
    climb_density = (
        analysis.elevation_gain_m / analysis.distance_km
        if analysis.distance_km > 0
        else None
    )
    timed_points = analysis.timed_points or []
    avg_vam = average_vam_m_per_h(analysis.elevation_gain_m, analysis.moving_time_seconds)
    best_vam = {
        "5min": best_vam_m_per_h(timed_points, 5 * 60),
        "20min": best_vam_m_per_h(timed_points, 20 * 60),
        "60min": best_vam_m_per_h(timed_points, 60 * 60),
    }
    return {
        "algorithm_version": ALGORITHM_VERSION,
        "point_count": analysis.analysis_json.get("point_count"),
        "effort_km": round(effort_km, 2),
        "climb_density_m_per_km": (
            round(climb_density, 2) if climb_density is not None else None
        ),
        "avg_vam_m_per_h": round(avg_vam, 1) if avg_vam is not None else None,
        "best_vam_5min_m_per_h": (
            round(best_vam["5min"], 1) if best_vam["5min"] is not None else None
        ),
        "best_vam_20min_m_per_h": (
            round(best_vam["20min"], 1) if best_vam["20min"] is not None else None
        ),
        "best_vam_60min_m_per_h": (
            round(best_vam["60min"], 1) if best_vam["60min"] is not None else None
        ),
        "has_time_data": analysis.moving_time_seconds is not None,
        "has_elevation_data": analysis.elevation_min_m is not None,
        "analysis_quality": analysis_quality(analysis),
        **_location_json(analysis.center_point),
    }


def calculate_profile_metrics(activities: list[ActivityTrack]) -> dict:
    count = len(activities)
    if count == 0:
        return {
            "level": "unknown",
            "endurance_score": None,
            "climb_score": None,
            "recent_max_distance_km": None,
            "recent_max_elevation_gain_m": None,
            "activity_count": 0,
            "confidence": "unknown",
            "metrics_json": {"algorithm_version": ALGORITHM_VERSION},
            "message": "暂无完成活动轨迹，无法生成能力画像。",
        }

    efforts = [activity.analysis_json.get("effort_km", 0) for activity in activities]
    max_effort = max(efforts)
    top3_effort = sum(sorted(efforts, reverse=True)[:3]) / min(3, count)
    weekly_effort = sum(efforts[:4]) / 4
    endurance_capacity = 0.60 * max_effort + 0.25 * top3_effort + 0.15 * weekly_effort
    endurance_score = normalize(endurance_capacity, 5, 35)

    gains = [activity.elevation_gain_m for activity in activities]
    densities = [
        activity.analysis_json.get("climb_density_m_per_km")
        for activity in activities
        if activity.analysis_json.get("climb_density_m_per_km") is not None
    ]
    vam20 = [
        activity.analysis_json.get("best_vam_20min_m_per_h")
        for activity in activities
        if activity.analysis_json.get("best_vam_20min_m_per_h") is not None
    ]
    vam60 = [
        activity.analysis_json.get("best_vam_60min_m_per_h")
        for activity in activities
        if activity.analysis_json.get("best_vam_60min_m_per_h") is not None
    ]
    avg_vam = [
        activity.analysis_json.get("avg_vam_m_per_h")
        for activity in activities
        if activity.analysis_json.get("avg_vam_m_per_h") is not None
    ]

    gain_score = normalize(percentile(gains, 90), 200, 1800)
    density_score = normalize(percentile(densities, 90) if densities else 0, 20, 120)
    if vam20 or vam60 or avg_vam:
        climb_score = (
            0.30 * gain_score
            + 0.20 * density_score
            + 0.20 * normalize(max(vam20) if vam20 else 0, 250, 900)
            + 0.20 * normalize(max(vam60) if vam60 else 0, 200, 700)
            + 0.10 * normalize(max(avg_vam) if avg_vam else 0, 150, 600)
        )
    else:
        climb_score = 0.70 * gain_score + 0.30 * density_score

    safe_score = min(endurance_score, climb_score)
    if safe_score < 0.35:
        level = "beginner"
    elif safe_score < 0.70:
        level = "normal"
    else:
        level = "strong"

    metrics_json = {
        "algorithm_version": ALGORITHM_VERSION,
        "recent_max_effort_km": round(max_effort, 2),
        "endurance_capacity_effort_km": round(endurance_capacity, 2),
        "best_vam_5min_m_per_h": max_json_metric(activities, "best_vam_5min_m_per_h"),
        "best_vam_20min_m_per_h": max_json_metric(activities, "best_vam_20min_m_per_h"),
        "best_vam_60min_m_per_h": max_json_metric(activities, "best_vam_60min_m_per_h"),
        "typical_vam_60min_m_per_h": (
            round(percentile(vam60, 75), 1) if vam60 else None
        ),
        "avg_climb_speed_m_per_min": (
            round((max(avg_vam) / 60), 1) if avg_vam else None
        ),
    }
    confidence_value = confidence(count, activities)
    return {
        "level": level,
        "endurance_score": round(endurance_score, 4),
        "climb_score": round(climb_score, 4),
        "recent_max_distance_km": max(activity.distance_km for activity in activities),
        "recent_max_elevation_gain_m": max(gains),
        "activity_count": count,
        "confidence": confidence_value,
        "metrics_json": metrics_json,
        "message": ability_message(count, confidence_value),
    }


def effort_distance_km(distance_km: float, elevation_gain_m: float) -> float:
    return distance_km + elevation_gain_m / 120


def average_vam_m_per_h(elevation_gain_m: float, seconds: int | None) -> float | None:
    if not seconds or seconds <= 0:
        return None
    return elevation_gain_m / (seconds / 3600)


def best_vam_m_per_h(points: list[TrackPoint], window_seconds: int) -> float | None:
    timed = [point for point in points if point.time is not None and point.ele is not None]
    if len(timed) < 2:
        return None

    best = 0.0
    start = 0
    for end, end_point in enumerate(timed):
        while start < end:
            seconds = (end_point.time - timed[start].time).total_seconds()
            if seconds <= window_seconds:
                break
            start += 1
        if start == end:
            continue
        seconds = (end_point.time - timed[start].time).total_seconds()
        if seconds <= 0:
            continue
        gain = max(0.0, (end_point.ele or 0) - (timed[start].ele or 0))
        if seconds >= window_seconds * 0.5:
            best = max(best, gain / (seconds / 3600))
    return best or None


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[int(index)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def max_json_metric(activities: list[ActivityTrack], key: str) -> float | None:
    values = [
        activity.analysis_json.get(key)
        for activity in activities
        if activity.analysis_json.get(key) is not None
    ]
    return max(values) if values else None


def confidence(count: int, activities: list[ActivityTrack]) -> str:
    if count == 0:
        return "unknown"
    good_quality_count = sum(
        1 for activity in activities if activity.analysis_json.get("analysis_quality") == "good"
    )
    if count <= 2:
        return "low" if good_quality_count < 2 else "medium"
    if count <= 4:
        return "medium"
    return "high"


def ability_message(count: int, confidence_value: str) -> str:
    confidence_labels = {
        "unknown": "未知",
        "low": "低",
        "medium": "中",
        "high": "高",
    }
    label = confidence_labels.get(confidence_value, confidence_value)
    return f"当前能力画像基于 {count} 条完成活动轨迹生成，可信度为{label}。"


def analysis_quality(analysis: TrackAnalysis) -> str:
    if analysis.moving_time_seconds and analysis.elevation_min_m is not None:
        return "good"
    if analysis.elevation_min_m is not None:
        return "medium"
    return "low"


def _location_json(center_point: dict) -> dict:
    lon = center_point.get("lon")
    lat = center_point.get("lat")
    if not isinstance(lon, int | float) or not isinstance(lat, int | float):
        return {}
    location = reverse_geocode_wgs84(float(lon), float(lat))
    if not location:
        return {}
    return {"location": location}


def _activity_date_from_analysis(analysis: TrackAnalysis) -> date | None:
    points = analysis.timed_points or []
    for point in points:
        if point.time:
            return point.time.date()
    return None


def _save_activity_file(user_id: str, track_id: str, file_type: str, content: bytes) -> str:
    extension = ".geojson" if file_type == "geojson" else f".{file_type}"
    storage_root = Path(get_settings().activity_storage_dir)
    activity_dir = storage_root / user_id
    activity_dir.mkdir(parents=True, exist_ok=True)
    file_path = activity_dir / f"{track_id}{extension}"
    file_path.write_bytes(content)
    return f"/static/activity-tracks/{user_id}/{track_id}{extension}"
