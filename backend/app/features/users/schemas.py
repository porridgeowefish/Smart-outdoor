from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    nickname: str
    avatar_url: str | None
    role: str


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    nickname: str
    avatar_url: str | None
    role: str
    status: str
    created_at: datetime
    last_login_at: datetime | None = None


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=500)


class ActivityAnalysisResponse(BaseModel):
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float | None
    elevation_min_m: float | None
    elevation_max_m: float | None
    moving_time_seconds: int | None
    analysis_json: dict


class AbilityProfileResponse(BaseModel):
    level: str
    endurance_score: float | None
    climb_score: float | None
    recent_max_distance_km: float | None
    recent_max_elevation_gain_m: float | None
    activity_count: int
    confidence: str
    generated_from_activity_track_ids: list[str]
    metrics_json: dict
    message: str | None = None


class ActivityUploadResponse(BaseModel):
    activity_track_id: str
    parse_status: str
    analysis: ActivityAnalysisResponse
    ability_profile: AbilityProfileResponse


class ActivityTrackItem(BaseModel):
    id: str
    month: str
    distance_km: float
    elevation_gain_m: float
    moving_time_seconds: int | None
    pace_or_speed: str
    activity_date: date
    location: str
    type: str
    analysis_json: dict


class ActivityTrackListResponse(BaseModel):
    tracks: list[ActivityTrackItem]
