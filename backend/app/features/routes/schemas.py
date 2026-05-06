"""线路相关的请求/响应 Pydantic 模型。

所有模型对应 OpenAPI 文档中的 schema，前端从 /openapi.json 生成 TypeScript 类型。"""

from __future__ import annotations

from pydantic import BaseModel


class RouteUploadResponse(BaseModel):
    """线路上传结果：返回线路ID、文件ID和解析状态。"""
    route_id: str
    file_id: str
    parse_status: str  # pending / parsed / failed
    parse_error: str | None = None


class Pagination(BaseModel):
    """分页元数据。"""
    page: int
    page_size: int
    total: int


class RouteListItem(BaseModel):
    """线路列表中的单条摘要信息。"""
    route_id: str
    name: str
    cover_image_url: str | None
    location: str
    visibility: str
    distance_km: float
    elevation_gain_m: float
    manual_tags: dict  # 原始标签（按分类）
    display_tags: list[str]  # 扁平化后的展示标签（最多 limit 个）


class RouteListResponse(BaseModel):
    items: list[RouteListItem]
    pagination: Pagination


class RouteAnalysisResponse(BaseModel):
    """线路分析指标：距离、海拔、坡度、起终点、边界框等。"""
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
    """线路轨迹数据：简化后的 GeoJSON LineString，用于前端地图渲染。"""
    format: str  # 固定 "geojson"
    coordinate_system: str  # 固定 "wgs84"
    simplified: bool  # 固定 true
    point_count: int
    geojson: dict


class RoutePrimaryFileResponse(BaseModel):
    """线路主文件信息：用户上传的原始轨迹文件。"""
    file_id: str
    file_type: str  # gpx / kml / geojson
    file_url: str
    parse_status: str


class RouteActionsResponse(BaseModel):
    """当前用户对该线路可执行的操作。"""
    can_send_to_trip_plan: bool
    can_download_file: bool
    can_edit: bool  # 仅创建者或管理员可编辑


class RouteDetailResponse(BaseModel):
    """线路详情：聚合元数据、分析指标、轨迹数据和权限信息。"""
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
    track: RouteTrackResponse
    primary_file: RoutePrimaryFileResponse
    actions: RouteActionsResponse
