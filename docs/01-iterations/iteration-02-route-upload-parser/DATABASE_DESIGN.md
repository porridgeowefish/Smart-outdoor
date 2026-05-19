# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

> Superseded by Iteration 07: 文件存储字段在 Iteration 07 改为 storage provider / storage key / URL metadata 契约，并新增派生 GeoJSON 存储规则。当前文件保留 Iteration 02 历史交付边界。

## route_assets

线路资产主档。

关键字段：

```text
id
name
description
cover_image_url
manual_tags
source_type
visibility
status
created_by_user_id
created_at
updated_at
```

## route_files

原始轨迹文件。

关键字段：

```text
id
route_asset_id
file_url
file_type
file_size_bytes
checksum
uploaded_by_user_id
parse_status
parse_error
created_at
updated_at
```

## route_analysis_snapshots

解析后的线路技术指标和渲染轨迹。

关键字段：

```text
id
route_asset_id
route_file_id
distance_km
elevation_gain_m
elevation_loss_m
elevation_min_m
elevation_max_m
climb_ratio
steep_ratio
start_point
end_point
bounds
center_point
track_geojson
analysis_json
created_at
```

## 规则

```text
原始文件只存在 route_files
日常地图渲染使用 route_analysis_snapshots.track_geojson
技术指标不放 route_assets
解析失败时 route_file.parse_status = failed
```
