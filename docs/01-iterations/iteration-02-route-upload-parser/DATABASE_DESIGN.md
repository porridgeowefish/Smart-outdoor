# Database Design

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM model and migrations; storage fields extended by Iteration 07.

> Superseded by Iteration 07: 文件存储字段在 Iteration 07 改为 storage provider / storage key / URL metadata 契约，并新增派生 GeoJSON 存储规则。当前文件保留 Iteration 02 历史交付边界。

## 表

```text
新增 route_assets。
新增 route_files。
新增 route_analysis_snapshots。
```

## route_assets

线路资产主档。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key，default uuid4 | 新增 |
| name | str | 线路名称，≤120 字符 | required | 新增 |
| description | str\|null | 线路描述 | nullable | 新增 |
| cover_image_url | str\|null | 封面图 URL，≤500 字符 | nullable；iter07 后由 storage metadata 派生 | 新增 |
| manual_tags | object | `{"地形": ["山地","丘陵"], "难度": ["中等"]}`：键分类 str，值标签 list[str] | default `{}` | 新增 |
| source_type | str | `"user_upload"` 等 | default `"user_upload"` | 新增 |
| visibility | str | `"public"` / `"private"` | default `"private"` | 新增 |
| status | str | `"active"` / `"deleted"` | default `"active"` | 新增 |
| created_by_user_id | str | 上传用户 ID | index | 新增 |
| created_at | datetime | 创建时间（UTC） | server generated | 新增 |
| updated_at | datetime | 更新时间（UTC） | server generated，onupdate | 新增 |

## route_files

原始轨迹文件记录。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key，default uuid4 | 新增 |
| route_asset_id | str | 关联线路资产 ID | foreign key: route_assets.id，index | 新增 |
| file_url | str | 文件 URL，≤500 字符 | required | 新增 |
| file_type | str | `"gpx"` / `"kml"` / `"geojson"` | required | 新增 |
| file_size_bytes | int\|null | 文件字节数 | nullable | 新增 |
| checksum | str\|null | SHA-256，≤64 字符 | nullable | 新增 |
| uploaded_by_user_id | str | 上传用户 ID | index | 新增 |
| parse_status | str | `"pending"` / `"parsed"` / `"failed"` | default `"pending"` | 新增 |
| parse_error | str\|null | 失败原因，目前固定 `"TRACK_PARSE_FAILED"` | nullable | 新增 |
| created_at | datetime | 创建时间（UTC） | server generated | 新增 |
| updated_at | datetime | 更新时间（UTC） | server generated，onupdate | 新增 |

## route_analysis_snapshots

解析后的技术指标和渲染轨迹。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key，default uuid4 | 新增 |
| route_asset_id | str | 关联线路资产 ID | foreign key: route_assets.id，index | 新增 |
| route_file_id | str | 关联原始文件 ID | foreign key: route_files.id，index | 新增 |
| distance_km | float | 距离（公里） | required | 新增 |
| elevation_gain_m | float | 累计爬升（米） | required | 新增 |
| elevation_loss_m | float\|null | 累计下降（米） | nullable | 新增 |
| elevation_min_m | float\|null | 最低海拔（米） | nullable | 新增 |
| elevation_max_m | float\|null | 最高海拔（米） | nullable | 新增 |
| climb_ratio | float\|null | 爬升 / 距离 | nullable | 新增 |
| steep_ratio | float\|null | 陡坡占比 | nullable；当前实现恒 null | 新增 |
| start_point | object | `{lon:float, lat:float, ele:float\|null}` | required | 新增 |
| end_point | object | `{lon:float, lat:float, ele:float\|null}` | required | 新增 |
| bounds | object | `{min_lon:float, min_lat:float, max_lon:float, max_lat:float}` | required | 新增 |
| center_point | object | `{lon:float, lat:float}` | required | 新增 |
| track_geojson | object | GeoJSON LineString：`{type:"LineString", coordinates:[[lon,lat,ele?], ...]}` | required | 新增 |
| analysis_json | object | 扩展分析数据（point_count / has_time_data / has_elevation_data / elapsed/rest/moving_time_seconds 等） | default `{}` | 新增 |
| created_at | datetime | 创建时间（UTC） | server generated | 新增 |

> iter07 新增字段（storage provider/key、preview、URL 等派生存储）不属于本轮范围，见 iter07 文档。

## 约束

```text
原始文件只存在 route_files。
地图渲染使用 route_analysis_snapshots.track_geojson。
技术指标不放 route_assets。
解析失败时 route_file.parse_status="failed"，不创建 route_analysis_snapshot。
manual_tags 必须为 JSON object，否则拒绝。
```

## 迁移与同步点

```text
新增 route_assets / route_files / route_analysis_snapshots 三张表。
iter07 将 file_url 形态切换为 storage provider/key/URL metadata，须同步读取点。
```

## 历史来源

- [iteration-07 DATABASE_DESIGN](../iteration-07-object-storage-image-assets/DATABASE_DESIGN.md)（存储字段扩展）
- `backend/app/features/routes/model.py`（ORM 事实源）
