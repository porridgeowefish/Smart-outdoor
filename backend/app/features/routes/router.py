"""线路 CRUD 接口：列表查询、上传、详情获取。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.routes.schemas import (
    Pagination,
    RouteActionsResponse,
    RouteAnalysisResponse,
    RouteDetailResponse,
    RouteListItem,
    RouteListResponse,
    RoutePrimaryFileResponse,
    RouteTagTaxonomyResponse,
    RouteTrackResponse,
    RouteUploadResponse,
)
from app.features.routes.service import (
    InvalidManualTagsError,
    RouteNotFoundError,
    UnsupportedCoverImageTypeError,
    UnsupportedRouteFileTypeError,
    build_track_preview,
    display_tags_from_manual_tags,
    get_visible_route_detail,
    list_visible_routes,
    upload_route,
)
from app.features.routes.tag_taxonomy import taxonomy_categories
from app.features.users.deps import get_current_user
from app.features.users.model import User

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=RouteListResponse)
def list_routes(
    keyword: str | None = None,
    visibility: str = "all",
    min_distance_km: float | None = None,
    max_distance_km: float | None = None,
    min_elevation_gain_m: float | None = None,
    max_elevation_gain_m: float | None = None,
    tags: str | None = None,
    tag_match_mode: str = "any",
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RouteListResponse:
    """查询线路列表，支持关键词、可见性、标签、距离和爬升范围过滤。

    过滤策略：先通过 DB 查询 + 内存过滤得到完整结果集，
    再在内存中对距离/爬升指标进行范围过滤（这些指标存在 snapshot 表中），
    最后手动分页返回。
    """
    # 先查全量（page_size=10000），因为距离/爬升指标在 snapshot 表中无法直接 SQL 过滤
    route_pairs, total_before_metric_filters = list_visible_routes(
        db,
        current_user,
        keyword=keyword,
        visibility=visibility,
        tags=tags,
        tag_match_mode=tag_match_mode,
        page=1,
        page_size=10_000,
    )
    # 内存中对距离和爬升指标做范围过滤
    metric_filtered = [
        (route, analysis)
        for route, analysis in route_pairs
        if _metric_filters_match(
            analysis.distance_km,
            analysis.elevation_gain_m,
            min_distance_km,
            max_distance_km,
            min_elevation_gain_m,
            max_elevation_gain_m,
        )
    ]
    total = len(metric_filtered)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    items = [
        RouteListItem(
            route_id=route.id,
            name=route.name,
            cover_image_url=route.cover_image_url,
            location=_route_location(route.manual_tags or {}, analysis.analysis_json or {}),
            visibility=route.visibility,
            distance_km=analysis.distance_km,
            elevation_gain_m=analysis.elevation_gain_m,
            manual_tags=route.manual_tags or {},
            display_tags=display_tags_from_manual_tags(route.manual_tags or {}),
            track_preview=build_track_preview(analysis),
        )
        for route, analysis in metric_filtered[start:end]
    ]
    return RouteListResponse(
        items=items,
        pagination=Pagination(page=page, page_size=page_size, total=total),
    )


@router.post("/upload", response_model=RouteUploadResponse)
async def upload_route_file(
    file: UploadFile = File(...),
    cover_image: UploadFile | None = File(default=None),
    name: str = Form(...),
    description: str | None = Form(default=None),
    visibility: str = Form(default="private"),
    manual_tags: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传线路轨迹文件（GPX/KML/GeoJSON），可选同时上传封面图片。"""
    try:
        route, route_file = await upload_route(
            db=db,
            current_user=current_user,
            file=file,
            name=name,
            description=description,
            visibility=visibility,
            manual_tags_raw=manual_tags,
            cover_image=cover_image,
        )
    except UnsupportedRouteFileTypeError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": "Only GPX, KML, and GeoJSON route files are supported",
            },
        )
    except InvalidManualTagsError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "INVALID_MANUAL_TAGS",
                "message": "manual_tags must be a JSON object",
            },
        )
    except UnsupportedCoverImageTypeError:
        return JSONResponse(
            status_code=400,
            content={
                "code": "UNSUPPORTED_COVER_IMAGE_TYPE",
                "message": "Only JPEG, PNG, and WebP cover images are supported",
            },
        )

    return RouteUploadResponse(
        route_id=route.id,
        file_id=route_file.id,
        parse_status=route_file.parse_status,
        parse_error=route_file.parse_error,
    )


@router.get("/tag-taxonomy", response_model=RouteTagTaxonomyResponse)
def get_route_tag_taxonomy() -> RouteTagTaxonomyResponse:
    return RouteTagTaxonomyResponse(categories=taxonomy_categories())


@router.get("/{route_id}", response_model=RouteDetailResponse)
def get_route_detail(
    route_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RouteDetailResponse:
    """获取线路详情，包含元数据、分析指标、轨迹数据和操作权限。"""
    try:
        route, analysis, route_file = get_visible_route_detail(db, current_user, route_id)
    except RouteNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"code": "ROUTE_NOT_FOUND", "message": "Route not found"},
        )

    coordinates = analysis.track_geojson.get("coordinates", [])
    return RouteDetailResponse(
        route_id=route.id,
        name=route.name,
        description=route.description,
        cover_image_url=route.cover_image_url,
        location=_route_location(route.manual_tags or {}, analysis.analysis_json or {}),
        visibility=route.visibility,
        source_type=route.source_type,
        source_name=route.source_name,
        manual_tags=route.manual_tags or {},
        analysis=RouteAnalysisResponse(
            route_analysis_snapshot_id=analysis.id,
            distance_km=analysis.distance_km,
            elevation_gain_m=analysis.elevation_gain_m,
            elevation_loss_m=analysis.elevation_loss_m,
            elevation_min_m=analysis.elevation_min_m,
            elevation_max_m=analysis.elevation_max_m,
            climb_ratio=analysis.climb_ratio,
            steep_ratio=analysis.steep_ratio,
            start_point=analysis.start_point,
            end_point=analysis.end_point,
            bounds=analysis.bounds,
            center_point=analysis.center_point,
            analysis_json=analysis.analysis_json or {},
        ),
        track=RouteTrackResponse(
            format="geojson",
            coordinate_system="wgs84",
            simplified=True,
            point_count=len(coordinates),
            geojson=analysis.track_geojson,
        ),
        primary_file=RoutePrimaryFileResponse(
            file_id=route_file.id,
            file_type=route_file.file_type,
            file_url=route_file.file_url,
            parse_status=route_file.parse_status,
        ),
        actions=RouteActionsResponse(
            can_send_to_trip_plan=True,
            can_download_file=False,
            # 仅创建者或管理员可编辑
            can_edit=route.created_by_user_id == current_user.id
            or current_user.role == "admin",
        ),
    )


def _metric_filters_match(
    distance_km: float,
    elevation_gain_m: float,
    min_distance_km: float | None,
    max_distance_km: float | None,
    min_elevation_gain_m: float | None,
    max_elevation_gain_m: float | None,
) -> bool:
    """检查线路的距离和爬升指标是否在指定范围内。"""
    if min_distance_km is not None and distance_km < min_distance_km:
        return False
    if max_distance_km is not None and distance_km > max_distance_km:
        return False
    if min_elevation_gain_m is not None and elevation_gain_m < min_elevation_gain_m:
        return False
    if max_elevation_gain_m is not None and elevation_gain_m > max_elevation_gain_m:
        return False
    return True


def _route_location(manual_tags: dict, analysis_json: dict) -> str:
    location = analysis_json.get("location")
    if isinstance(location, dict) and isinstance(location.get("display_name"), str):
        return location["display_name"]

    for key in ("location", "region", "行政区", "地区"):
        value = manual_tags.get(key)
        if isinstance(value, list) and value:
            return " · ".join(str(item) for item in value if str(item).strip())
        if isinstance(value, str) and value.strip():
            return value.strip()

    return "待识别"
