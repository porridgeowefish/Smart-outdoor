"""线路相关 ORM 模型。

三张表各司其职：
- RouteAsset：线路资产元数据（名称、标签、可见性等）
- RouteFile：用户上传的原始轨迹文件
- RouteAnalysisSnapshot：解析后的指标和简化 GeoJSON（用于前端渲染和推荐筛选）
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RouteAsset(Base):
    """线路资产表：存储线路的元数据，不包含轨迹坐标。

    visibility 取值：public / private
    status 取值：active / deleted
    manual_tags 结构：{"地形": ["山地", "丘陵"], "难度": ["中等"]}，键为分类，值为标签列表
    """
    __tablename__ = "route_assets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_storage_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cover_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_variants: Mapped[dict] = mapped_column(JSON, default=dict)
    cover_original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_processing_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manual_tags: Mapped[dict] = mapped_column(JSON, default=dict)
    source_type: Mapped[str] = mapped_column(String(32), default="user_upload")
    source_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="private")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_by_user_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )


class RouteFile(Base):
    """线路文件表：记录用户上传的原始轨迹文件（KML/GPX/GeoJSON）。

    parse_status 取值：pending / parsed / failed
    """
    __tablename__ = "route_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    route_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("route_assets.id"), index=True
    )
    file_url: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(32))  # gpx / kml / geojson
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    storage_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by_user_id: Mapped[str] = mapped_column(String(36), index=True)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )


class RouteAnalysisSnapshot(Base):
    """线路分析快照表：保存轨迹解析后的指标和简化 GeoJSON。

    前端地图渲染使用 track_geojson，不直接解析原始 KML/GPX 文件。
    距离/海拔/坡度指标用于线路筛选和 Agent 推荐。
    """
    __tablename__ = "route_analysis_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    route_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("route_assets.id"), index=True
    )
    route_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("route_files.id"), index=True
    )
    distance_km: Mapped[float] = mapped_column(Float)
    elevation_gain_m: Mapped[float] = mapped_column(Float)
    elevation_loss_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_min_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_max_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    climb_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # 爬升/距离，用于难度评估
    steep_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # 陡坡占比
    start_point: Mapped[dict] = mapped_column(JSON)  # {"lon": ..., "lat": ..., "ele": ...}
    end_point: Mapped[dict] = mapped_column(JSON)
    bounds: Mapped[dict] = mapped_column(JSON)  # {"min_lon", "min_lat", "max_lon", "max_lat"}
    center_point: Mapped[dict] = mapped_column(JSON)
    track_geojson: Mapped[dict] = mapped_column(JSON)  # 简化后的 LineString GeoJSON，用于前端渲染
    track_preview_geojson: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    track_preview_point_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_geojson_storage_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    track_geojson_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    track_geojson_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    track_geojson_point_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_geojson_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 扩展分析数据（如点数统计）
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
