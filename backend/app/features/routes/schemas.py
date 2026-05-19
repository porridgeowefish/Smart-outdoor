"""Pydantic schemas for route APIs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.features.storage.schemas import ImageAssetMetadata


class RouteTrackPreviewResponse(BaseModel):
    format: str
    coordinate_system: str
    point_count: int
    geojson: dict


class RouteTagCategoryResponse(BaseModel):
    key: str
    label: str
    tags: list[str]


class RouteTagTaxonomyResponse(BaseModel):
    categories: list[RouteTagCategoryResponse]


class TrackFileMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_provider: str = Field(min_length=1, max_length=32)
    storage_key: str = Field(min_length=1, max_length=500)
    file_url: str = Field(min_length=1, max_length=500)
    file_type: str = Field(min_length=1, max_length=32)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(ge=0)
    original_filename: str = Field(min_length=1, max_length=255)


class RouteUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    visibility: str = Field(default="private", max_length=32)
    manual_tags: dict | None = None
    track_file: TrackFileMetadata
    cover_image: ImageAssetMetadata | None = None


class RouteUploadResponse(BaseModel):
    route_id: str
    file_id: str
    parse_status: str
    parse_error: str | None = None


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int


class RouteListItem(BaseModel):
    route_id: str
    name: str
    cover_image_url: str | None
    location: str
    visibility: str
    distance_km: float
    elevation_gain_m: float
    manual_tags: dict
    display_tags: list[str]
    track_preview: RouteTrackPreviewResponse | None = None


class RouteListResponse(BaseModel):
    items: list[RouteListItem]
    pagination: Pagination


class RouteAnalysisResponse(BaseModel):
    route_analysis_snapshot_id: str
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float | None
    elevation_min_m: float | None
    elevation_max_m: float | None
    climb_ratio: float | None
    steep_ratio: float | None
    start_point: dict
    end_point: dict
    bounds: dict
    center_point: dict
    analysis_json: dict


class RouteTrackResponse(BaseModel):
    format: str
    coordinate_system: str
    source: str
    point_count: int
    track_url: str
    geojson: dict | None = None


class RouteFullTrackResponse(BaseModel):
    format: str
    coordinate_system: str
    source: str
    point_count: int
    geojson: dict


class RoutePrimaryFileResponse(BaseModel):
    file_id: str
    file_type: str
    file_url: str
    parse_status: str


class RouteActionsResponse(BaseModel):
    can_send_to_trip_plan: bool
    can_download_file: bool
    can_edit: bool


class RouteDetailResponse(BaseModel):
    route_id: str
    name: str
    description: str | None
    cover_image_url: str | None
    location: str
    visibility: str
    source_type: str
    source_name: str | None
    manual_tags: dict
    analysis: RouteAnalysisResponse
    track_preview: RouteTrackPreviewResponse | None = None
    track: RouteTrackResponse
    primary_file: RoutePrimaryFileResponse
    actions: RouteActionsResponse
