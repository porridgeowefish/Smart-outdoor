from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.routes.service import UnsupportedRouteFileTypeError
from app.features.users.activity_service import (
    ActivityTrackParseError,
    get_user_ability_profile,
    list_user_activity_tracks,
    upload_activity_track,
)
from app.features.users.deps import get_current_user
from app.features.users.model import ActivityTrack, User, UserAbilityProfile
from app.features.users.schemas import (
    AbilityProfileResponse,
    ActivityAnalysisResponse,
    ActivityTrackItem,
    ActivityTrackListResponse,
    ActivityUploadResponse,
    UserMe,
    UserUpdateRequest,
)
from app.features.users.service import (
    InvalidAvatarFileError,
    update_user_avatar,
    update_user_profile,
)

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserMe)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserMe)
def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return update_user_profile(db, current_user, payload)


@router.post("/me/avatar", response_model=UserMe)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return await update_user_avatar(db, current_user, file)
    except InvalidAvatarFileError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "INVALID_AVATAR_FILE",
                "message": "仅支持 JPG、PNG、WebP 或 GIF 图片",
            },
        )


@router.post("/me/activity-tracks/upload", response_model=ActivityUploadResponse)
async def upload_my_activity_track(
    file: UploadFile = File(...),
    activity_date: date | None = Form(default=None),
    source_type: str = Form(default="manual_upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        activity, profile = await upload_activity_track(
            db=db,
            current_user=current_user,
            file=file,
            activity_date=activity_date,
            source_type=source_type,
        )
    except UnsupportedRouteFileTypeError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "Only GPX, KML, and GeoJSON activity tracks are supported",
            },
        )
    except ActivityTrackParseError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "TRACK_PARSE_FAILED",
                "message": "Activity track could not be parsed",
            },
        )

    return ActivityUploadResponse(
        activity_track_id=activity.id,
        parse_status="parsed",
        analysis=_activity_analysis_response(activity),
        ability_profile=_ability_profile_response(profile),
    )


@router.get("/me/activity-tracks", response_model=ActivityTrackListResponse)
def list_my_activity_tracks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityTrackListResponse:
    activities = list_user_activity_tracks(db, current_user)
    return ActivityTrackListResponse(
        tracks=[_activity_track_item(activity) for activity in activities]
    )


@router.get("/me/ability-profile", response_model=AbilityProfileResponse)
def read_my_ability_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_user_ability_profile(db, current_user)
    if profile is None:
        return JSONResponse(
            status_code=404,
            content={
                "code": "ABILITY_PROFILE_NOT_FOUND",
                "message": "Ability profile not found",
            },
        )
    return _ability_profile_response(profile)


def _activity_analysis_response(activity: ActivityTrack) -> ActivityAnalysisResponse:
    return ActivityAnalysisResponse(
        distance_km=activity.distance_km,
        elevation_gain_m=activity.elevation_gain_m,
        elevation_loss_m=activity.elevation_loss_m,
        elevation_min_m=activity.elevation_min_m,
        elevation_max_m=activity.elevation_max_m,
        moving_time_seconds=activity.moving_time_seconds,
        analysis_json=activity.analysis_json or {},
    )


def _ability_profile_response(profile: UserAbilityProfile) -> AbilityProfileResponse:
    return AbilityProfileResponse(
        level=profile.level,
        endurance_score=profile.endurance_score,
        climb_score=profile.climb_score,
        recent_max_distance_km=profile.recent_max_distance_km,
        recent_max_elevation_gain_m=profile.recent_max_elevation_gain_m,
        activity_count=profile.activity_count,
        confidence=profile.confidence,
        generated_from_activity_track_ids=profile.generated_from_activity_track_ids or [],
        metrics_json=profile.metrics_json or {},
        message=profile.message,
    )


def _activity_track_item(activity: ActivityTrack) -> ActivityTrackItem:
    return ActivityTrackItem(
        id=activity.id,
        month=str(activity.activity_date.month),
        distance_km=activity.distance_km,
        elevation_gain_m=activity.elevation_gain_m,
        moving_time_seconds=activity.moving_time_seconds,
        pace_or_speed=_pace_or_speed(activity),
        activity_date=activity.activity_date,
        location=_activity_location(activity.analysis_json or {}),
        type="hike",
        analysis_json=activity.analysis_json or {},
    )


def _pace_or_speed(activity: ActivityTrack) -> str:
    seconds = activity.moving_time_seconds
    if not seconds or activity.distance_km <= 0:
        return "--"
    minutes_per_km = seconds / 60 / activity.distance_km
    minutes = int(minutes_per_km)
    seconds_part = int(round((minutes_per_km - minutes) * 60))
    if seconds_part == 60:
        minutes += 1
        seconds_part = 0
    return f"{minutes}'{seconds_part:02d}\" /km"


def _activity_location(analysis_json: dict) -> str:
    location = analysis_json.get("location")
    if isinstance(location, dict) and isinstance(location.get("display_name"), str):
        return location["display_name"]
    return "待识别"
