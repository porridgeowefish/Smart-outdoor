"""线路业务逻辑：上传、查询、可见性过滤、标签处理。"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.features.geo.amap_reverse_geocode import reverse_geocode_wgs84
from app.features.routes.model import (
    RouteAnalysisSnapshot,
    RouteAsset,
    RouteFile,
)
from app.features.routes.schemas import RouteUploadRequest
from app.features.routes.parser import TrackParseError, parse_track
from app.features.storage.service import (
    InvalidStorageObjectError,
    StorageObjectNotFoundError,
    get_storage_service,
    validate_key_for_user,
)
from app.features.users.model import User

_SUPPORTED_EXTENSIONS = {
    ".gpx": "gpx",
    ".kml": "kml",
    ".geojson": "geojson",
    ".json": "geojson",  # .json 文件视为 GeoJSON
}

_SUPPORTED_COVER_EXTENSIONS = {
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
    ".webp": "webp",
}

_SUPPORTED_COVER_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class UnsupportedRouteFileTypeError(Exception):
    """不支持的轨迹文件格式。"""
    pass


class UnsupportedCoverImageTypeError(Exception):
    """不支持的封面图片格式。"""
    pass


class InvalidManualTagsError(Exception):
    """manual_tags 不是合法的 JSON 对象。"""
    pass


class InvalidStorageMetadataError(Exception):
    """上传完成 metadata 不合法。"""
    pass


class StorageObjectMissingError(Exception):
    """storage_key 指向的对象不存在。"""
    pass


class RouteNotFoundError(Exception):
    """线路不存在或当前用户无权访问。"""
    pass


def detect_file_type(filename: str) -> str:
    """根据文件扩展名检测轨迹文件类型。不支持时抛出异常。"""
    extension = Path(filename).suffix.lower()
    file_type = _SUPPORTED_EXTENSIONS.get(extension)
    if file_type is None:
        raise UnsupportedRouteFileTypeError
    return file_type


def upload_route(
    db: Session,
    current_user: User,
    payload: RouteUploadRequest,
) -> tuple[RouteAsset, RouteFile]:
    """处理线路上传 complete：读取已直传文件 → 解析 → 生成资产和快照。

    即使轨迹解析失败，资产和文件记录仍然保留（parse_status="failed"），
    用户可以后续重新上传文件。
    """
    file_type = _validate_track_metadata(payload.track_file, current_user)
    manual_tags = payload.manual_tags or {}
    if not isinstance(manual_tags, dict):
        raise InvalidManualTagsError
    visibility_value = payload.visibility if payload.visibility in {"public", "private"} else "private"
    storage = get_storage_service()
    try:
        content = storage.read_bytes(
            key=payload.track_file.storage_key,
            provider=payload.track_file.storage_provider,
        )
    except StorageObjectNotFoundError as exc:
        raise StorageObjectMissingError from exc

    # 1. 创建线路资产记录
    route = RouteAsset(
        name=payload.name,
        description=payload.description,
        manual_tags=manual_tags,
        source_type="user_upload",
        visibility=visibility_value,
        status="active",
        created_by_user_id=current_user.id,
    )
    db.add(route)
    db.flush()

    # 2. 可选：保存前端已上传的封面 metadata
    if payload.cover_image is not None:
        _apply_cover_metadata(route, current_user, payload.cover_image)
        db.add(route)
        db.flush()

    # 3. 保存原始轨迹文件 metadata
    file_id = str(uuid.uuid4())
    route_file = RouteFile(
        id=file_id,
        route_asset_id=route.id,
        file_url=payload.track_file.file_url,
        file_type=file_type,
        file_size_bytes=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        storage_provider=payload.track_file.storage_provider,
        storage_key=payload.track_file.storage_key,
        content_type=payload.track_file.content_type,
        original_filename=payload.track_file.original_filename,
        uploaded_by_user_id=current_user.id,
        parse_status="pending",
    )
    db.add(route_file)
    db.flush()

    # 4. 解析轨迹并生成分析快照
    try:
        analysis = parse_track(content, file_type)
    except TrackParseError:
        # 解析失败：保留记录但标记为 failed，不阻断上传流程
        route_file.parse_status = "failed"
        route_file.parse_error = "TRACK_PARSE_FAILED"
        db.add(route_file)
        db.commit()
        db.refresh(route)
        db.refresh(route_file)
        return route, route_file

    full_geojson_content = json.dumps(analysis.track_geojson, ensure_ascii=False).encode("utf-8")
    derived_key = f"users/{current_user.id}/routes/{route.id}/derived/full.geojson"
    stored_full = storage.put_bytes(
        key=derived_key,
        content=full_geojson_content,
        content_type="application/geo+json",
        provider="local" if storage.provider == "local" else storage.provider,
    )
    preview_geojson = build_high_fidelity_preview(analysis.track_geojson)
    preview_count = len(preview_geojson.get("coordinates") or [])
    full_count = len(analysis.track_geojson.get("coordinates") or [])
    analysis_json = _analysis_json_with_location(analysis.analysis_json, analysis.center_point)
    analysis_json.update(
        {
            "preview_algorithm": "douglas_peucker_v1",
            "preview_tolerance_m": 10,
            "preview_max_segment_length_m": 150,
            "preview_point_count": preview_count,
            "full_point_count": full_count,
        }
    )
    snapshot = RouteAnalysisSnapshot(
        route_asset_id=route.id,
        route_file_id=route_file.id,
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
        track_geojson=preview_geojson,
        track_preview_geojson=preview_geojson,
        track_preview_point_count=preview_count,
        track_geojson_storage_provider=stored_full.provider,
        track_geojson_storage_key=stored_full.key,
        track_geojson_url=stored_full.url,
        track_geojson_point_count=full_count,
        track_geojson_size_bytes=stored_full.size_bytes,
        analysis_json=analysis_json,
    )
    route_file.parse_status = "parsed"
    route_file.parse_error = None
    db.add(snapshot)
    db.add(route_file)
    db.commit()
    db.refresh(route)
    db.refresh(route_file)
    return route, route_file


def _validate_track_metadata(track_file, current_user: User) -> str:
    try:
        validate_key_for_user(key=track_file.storage_key, user_id=current_user.id)
    except InvalidStorageObjectError as exc:
        raise InvalidStorageMetadataError from exc
    detected = detect_file_type(track_file.original_filename)
    if detected != track_file.file_type:
        raise UnsupportedRouteFileTypeError
    return detected


def _apply_cover_metadata(route: RouteAsset, current_user: User, cover) -> None:
    variants = cover.variants
    large = variants.get("large")
    if large is None:
        raise InvalidStorageMetadataError
    try:
        validate_key_for_user(key=cover.storage_key, user_id=current_user.id)
        for variant in variants.values():
            validate_key_for_user(key=variant.storage_key, user_id=current_user.id)
    except InvalidStorageObjectError as exc:
        raise InvalidStorageMetadataError from exc
    if cover.storage_key != large.storage_key or cover.url != large.url:
        raise InvalidStorageMetadataError
    route.cover_image_url = large.url
    route.cover_storage_provider = cover.storage_provider
    route.cover_storage_key = large.storage_key
    route.cover_image_variants = {
        key: value.model_dump() for key, value in variants.items()
    }
    route.cover_original_filename = cover.original_filename
    route.cover_processing_status = cover.processing_status


def _analysis_json_with_location(analysis_json: dict, center_point: dict) -> dict:
    enriched = dict(analysis_json or {})
    if enriched.get("location"):
        return enriched
    lon = center_point.get("lon")
    lat = center_point.get("lat")
    if not isinstance(lon, int | float) or not isinstance(lat, int | float):
        return enriched
    location = reverse_geocode_wgs84(float(lon), float(lat))
    if location:
        enriched["location"] = location
    return enriched


def _parse_manual_tags(raw: str | None) -> dict:
    """将 JSON 字符串解析为标签字典。空值返回空字典。"""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidManualTagsError from exc
    if not isinstance(parsed, dict):
        raise InvalidManualTagsError
    return parsed


def list_visible_routes(
    db: Session,
    current_user: User,
    *,
    keyword: str | None = None,
    visibility: str = "all",
    tags: str | None = None,
    tag_match_mode: str = "any",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[tuple[RouteAsset, RouteAnalysisSnapshot]], int]:
    """查询当前用户可见的线路列表，支持关键词、可见性、标签过滤。

    过滤顺序：status=active → 可见性 → visibility 筛选 → 关键词 → 标签匹配 → 分页。
    返回 (线路+分析快照列表, 过滤后总数)。
    """
    routes = (
        db.query(RouteAsset)
        .filter(RouteAsset.status == "active")
        .order_by(RouteAsset.created_at.desc())
        .all()
    )
    requested_tags = _parse_tags_query(tags)
    filtered: list[tuple[RouteAsset, RouteAnalysisSnapshot]] = []

    for route in routes:
        # 可见性：public 对所有人可见，private 仅创建者可见
        if not _is_route_visible_to_user(route, current_user):
            continue
        # 按 visibility 参数过滤
        if visibility == "public" and route.visibility != "public":
            continue
        if visibility == "private" and not (
            route.visibility == "private" and route.created_by_user_id == current_user.id
        ):
            continue
        # 关键词搜索：匹配名称或描述（不区分大小写）
        if keyword and keyword.lower() not in route.name.lower():
            description = route.description or ""
            if keyword.lower() not in description.lower():
                continue
        # 标签匹配：mode="any" 任一匹配，mode="all" 全部匹配
        if requested_tags and not _tags_match(
            route.manual_tags or {}, requested_tags, tag_match_mode
        ):
            continue
        analysis = get_latest_analysis_for_route(db, route.id)
        if analysis is None:
            continue
        filtered.append((route, analysis))

    total = len(filtered)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return filtered[start:end], total


def get_visible_route_detail(
    db: Session, current_user: User, route_id: str
) -> tuple[RouteAsset, RouteAnalysisSnapshot, RouteFile]:
    """获取线路详情，校验可见性后返回 (资产, 分析快照, 主文件) 三元组。"""
    route = db.get(RouteAsset, route_id)
    if route is None or not _is_route_visible_to_user(route, current_user):
        raise RouteNotFoundError
    analysis = get_latest_analysis_for_route(db, route_id)
    route_file = get_primary_file_for_route(db, route_id)
    if analysis is None or route_file is None:
        raise RouteNotFoundError
    return route, analysis, route_file


def get_latest_analysis_for_route(
    db: Session, route_id: str
) -> RouteAnalysisSnapshot | None:
    """获取线路最新一次解析的分析快照（按创建时间降序取第一条）。"""
    return (
        db.query(RouteAnalysisSnapshot)
        .filter(RouteAnalysisSnapshot.route_asset_id == route_id)
        .order_by(RouteAnalysisSnapshot.created_at.desc())
        .first()
    )


def get_primary_file_for_route(db: Session, route_id: str) -> RouteFile | None:
    """获取线路的主文件（最早上传的文件）。"""
    return (
        db.query(RouteFile)
        .filter(RouteFile.route_asset_id == route_id)
        .order_by(RouteFile.created_at.asc())
        .first()
    )


def get_full_track_geojson(analysis: RouteAnalysisSnapshot) -> dict:
    if analysis.track_geojson_storage_key:
        storage = get_storage_service()
        try:
            content = storage.read_bytes(
                key=analysis.track_geojson_storage_key,
                provider=analysis.track_geojson_storage_provider,
            )
        except StorageObjectNotFoundError as exc:
            raise StorageObjectMissingError from exc
        return json.loads(content.decode("utf-8"))
    return analysis.track_geojson or {}


def build_track_preview(analysis: RouteAnalysisSnapshot) -> dict | None:
    """Build a high-fidelity preview for route cards."""
    source = analysis.track_preview_geojson or analysis.track_geojson or {}
    coordinates = source.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    normalized = [_normalize_coordinate(item) for item in coordinates]
    normalized = [item for item in normalized if item]
    if len(normalized) < 2:
        return None
    return {
        "format": "geojson",
        "coordinate_system": "wgs84",
        "point_count": len(coordinates),
        "geojson": {"type": "LineString", "coordinates": normalized},
    }


def build_high_fidelity_preview(track_geojson: dict) -> dict:
    coordinates = track_geojson.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 3:
        return track_geojson
    normalized = [_normalize_coordinate(item) for item in coordinates]
    normalized = [item for item in normalized if item]
    simplified = _douglas_peucker(normalized, tolerance_m=10.0)
    protected = _protect_max_segment_length(simplified, max_segment_length_m=150.0)
    return {"type": "LineString", "coordinates": protected}


def display_tags_from_manual_tags(manual_tags: dict, limit: int = 3) -> list[str]:
    """将 manual_tags 扁平化为展示标签列表，默认最多返回 3 个。

    例如 {"地形": ["山地", "丘陵"], "难度": ["中等"]} → ["山地", "丘陵", "中等"]
    """
    tags = _flatten_tags(manual_tags)
    return tags[:limit]


def _sample_coordinates(coordinates: list, *, max_points: int) -> list[list[float]]:
    if len(coordinates) <= max_points:
        return [_normalize_coordinate(item) for item in coordinates if _normalize_coordinate(item)]
    if max_points < 2:
        max_points = 2
    last_index = len(coordinates) - 1
    sampled: list[list[float]] = []
    used_indexes: set[int] = set()
    for index in range(max_points):
        source_index = round(index * last_index / (max_points - 1))
        if source_index in used_indexes:
            continue
        used_indexes.add(source_index)
        normalized = _normalize_coordinate(coordinates[source_index])
        if normalized:
            sampled.append(normalized)
    return sampled


def _douglas_peucker(points: list[list[float]], *, tolerance_m: float) -> list[list[float]]:
    if len(points) <= 2:
        return points
    max_distance = -1.0
    index = 0
    start = points[0]
    end = points[-1]
    for current_index, point in enumerate(points[1:-1], start=1):
        distance = _point_to_segment_distance_m(point, start, end)
        if distance > max_distance:
            index = current_index
            max_distance = distance
    if max_distance > tolerance_m:
        left = _douglas_peucker(points[: index + 1], tolerance_m=tolerance_m)
        right = _douglas_peucker(points[index:], tolerance_m=tolerance_m)
        return left[:-1] + right
    return [start, end]


def _protect_max_segment_length(
    points: list[list[float]], *, max_segment_length_m: float
) -> list[list[float]]:
    if len(points) < 2:
        return points
    result = [points[0]]
    for start, end in zip(points, points[1:]):
        distance = _distance_m(start, end)
        steps = max(1, int(distance // max_segment_length_m) + (1 if distance % max_segment_length_m else 0))
        for step in range(1, steps):
            ratio = step / steps
            result.append(_interpolate_coordinate(start, end, ratio))
        result.append(end)
    return result


def _point_to_segment_distance_m(point: list[float], start: list[float], end: list[float]) -> float:
    px, py = _project_m(point, start)
    sx, sy = 0.0, 0.0
    ex, ey = _project_m(end, start)
    dx = ex - sx
    dy = ey - sy
    if dx == 0 and dy == 0:
        return (px**2 + py**2) ** 0.5
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
    nearest_x = sx + t * dx
    nearest_y = sy + t * dy
    return ((px - nearest_x) ** 2 + (py - nearest_y) ** 2) ** 0.5


def _project_m(point: list[float], origin: list[float]) -> tuple[float, float]:
    import math

    earth_radius_m = 6371008.8
    lon = math.radians(point[0])
    lat = math.radians(point[1])
    origin_lon = math.radians(origin[0])
    origin_lat = math.radians(origin[1])
    x = (lon - origin_lon) * math.cos((lat + origin_lat) / 2) * earth_radius_m
    y = (lat - origin_lat) * earth_radius_m
    return x, y


def _distance_m(start: list[float], end: list[float]) -> float:
    sx, sy = _project_m(start, start)
    ex, ey = _project_m(end, start)
    return ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5


def _interpolate_coordinate(start: list[float], end: list[float], ratio: float) -> list[float]:
    length = min(len(start), len(end))
    return [float(start[index]) + (float(end[index]) - float(start[index])) * ratio for index in range(length)]


def _normalize_coordinate(value: object) -> list[float]:
    if not isinstance(value, list | tuple) or len(value) < 2:
        return []
    lon = value[0]
    lat = value[1]
    if not isinstance(lon, int | float) or not isinstance(lat, int | float):
        return []
    result = [float(lon), float(lat)]
    if len(value) >= 3 and isinstance(value[2], int | float):
        result.append(float(value[2]))
    return result


def _is_route_visible_to_user(route: RouteAsset, user: User) -> bool:
    """判断线路对指定用户是否可见：公开线路所有人可见，私有线路仅创建者可见。"""
    return route.visibility == "public" or route.created_by_user_id == user.id


def _parse_tags_query(tags: str | None) -> list[str]:
    """将逗号分隔的标签字符串解析为列表。"""
    if not tags:
        return []
    return [item.strip() for item in tags.split(",") if item.strip()]


def _tags_match(manual_tags: dict, requested_tags: list[str], mode: str) -> bool:
    """检查线路标签是否匹配请求的标签。

    mode="any": 线路标签与请求标签有交集即匹配
    mode="all": 线路标签必须包含所有请求标签
    """
    route_tags = set(_flatten_tags(manual_tags))
    requested = set(requested_tags)
    if mode == "all":
        return requested.issubset(route_tags)
    return bool(route_tags.intersection(requested))


def _flatten_tags(manual_tags: dict) -> list[str]:
    """将 manual_tags 字典扁平化为标签值列表，忽略非列表值。"""
    flattened: list[str] = []
    for value in manual_tags.values():
        if isinstance(value, list):
            flattened.extend(str(item) for item in value)
    return flattened
