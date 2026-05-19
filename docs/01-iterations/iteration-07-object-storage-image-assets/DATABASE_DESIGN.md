# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: ORM models and migrations after implementation.

## 本轮改造目标

把文件字段从本地路径思维调整为统一存储资产契约，同时把完整轨迹渲染数据从数据库 JSON 迁移为对象存储派生文件。

```text
图片：数据库保存处理后版本 variants metadata，不保存上传原图。
原始轨迹：对象存储完整保存，数据库保存定位、checksum 和 metadata。
派生轨迹：full track_geojson 存对象存储，preview track_geojson 存数据库。
```

## users

保留字段：

```text
avatar_url
```

新增字段：

```text
avatar_storage_provider
avatar_storage_key
avatar_variants
avatar_original_filename
avatar_processing_status
```

规则：

```text
avatar_url = avatar_variants.display.url。
avatar_storage_key = avatar_variants.display.storage_key。
avatar_variants 是 JSON 字段，保存 display / thumbnail metadata。
avatar_original_filename 只保存上传文件名文本，不保存原图。
avatar_processing_status 本轮写 ready / failed。
```

`avatar_variants` 示例：

```json
{
  "display": {
    "storage_key": "users/user_1/avatar/display.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/display.webp",
    "width": 512,
    "height": 512,
    "content_type": "image/webp",
    "size_bytes": 123456
  },
  "thumbnail": {
    "storage_key": "users/user_1/avatar/thumbnail.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/thumbnail.webp",
    "width": 128,
    "height": 128,
    "content_type": "image/webp",
    "size_bytes": 30000
  }
}
```

不新增：

```text
avatar_original_url
avatar_original_storage_key
avatar_content_type
avatar_size_bytes
```

`content_type` 和 `size_bytes` 放在 variants 每个版本里。

## route_assets

保留字段：

```text
cover_image_url
```

新增字段：

```text
cover_storage_provider
cover_storage_key
cover_image_variants
cover_original_filename
cover_processing_status
```

规则：

```text
cover_image_url = cover_image_variants.large.url。
cover_storage_key = cover_image_variants.large.storage_key。
cover_image_variants 是 JSON 字段，保存 large / thumbnail metadata。
列表页优先使用 cover_image_variants.thumbnail.url。
详情页使用 cover_image_url / large.url。
cover_original_filename 只保存上传文件名文本，不保存原图。
cover_processing_status 本轮写 ready / failed。
```

`cover_image_variants` 示例：

```json
{
  "large": {
    "storage_key": "routes/route_1/cover/large.webp",
    "url": "https://cdn.example.com/routes/route_1/cover/large.webp",
    "width": 1280,
    "height": 720,
    "content_type": "image/webp",
    "size_bytes": 450000
  },
  "thumbnail": {
    "storage_key": "routes/route_1/cover/thumbnail.webp",
    "url": "https://cdn.example.com/routes/route_1/cover/thumbnail.webp",
    "width": 480,
    "height": 270,
    "content_type": "image/webp",
    "size_bytes": 100000
  }
}
```

不新增：

```text
cover_original_url
cover_original_storage_key
cover_content_type
cover_size_bytes
```

## route_files

保留字段：

```text
file_url
file_type
file_size_bytes
checksum
parse_status
parse_error
```

新增字段：

```text
storage_provider
storage_key
content_type
original_filename
```

规则：

```text
file_url 是原始轨迹文件可访问 URL。
storage_key 是后端内部读取、解析、下载和删除依据。
content_type 是上传对象的 MIME type。
original_filename 是用户上传时的原始文件名。
file_size_bytes 是原始文件大小。
checksum 由后端读取对象存储 bytes 后计算 SHA-256。
轨迹文件不做 variants。
轨迹文件不做 processing_status。
```

## route_analysis_snapshots

当前相关字段：

```text
track_geojson
analysis_json
```

新增字段：

```text
track_preview_geojson
track_preview_point_count
track_geojson_storage_provider
track_geojson_storage_key
track_geojson_url
track_geojson_point_count
track_geojson_size_bytes
```

规则：

```text
track_preview_geojson 存数据库，用于列表和详情初屏。
track_geojson_storage_key 指向对象存储中的完整派生 LineString GeoJSON。
track_geojson_url 是完整派生 GeoJSON 的可访问 URL 或受控 URL 基础信息。
track_geojson_point_count 是 full GeoJSON 点数。
track_geojson_size_bytes 是 full GeoJSON 文件大小。
旧 track_geojson 字段作为 legacy 字段保留；新数据不再把 full track_geojson 写入该字段。
```

preview metadata 写入 `analysis_json`：

```json
{
  "preview_algorithm": "douglas_peucker_v1",
  "preview_tolerance_m": 10,
  "preview_max_segment_length_m": 150,
  "preview_point_count": 420,
  "full_point_count": 12840
}
```

## Storage provider 取值

```text
local
object_storage
cos
```

本轮云端对象存储优先采用腾讯云 COS。`object_storage` 可作为抽象 provider 名称；具体落地和迁移记录可以使用 `cos`。

```text
oss
s3
minio
```

## 上传凭据记录

本轮可以先不新增持久化 upload credential 表；凭据由 provider 生成并带过期时间。

如果后续需要更强审计或回放校验，再新增表：

```text
storage_upload_intents
```

候选字段：

```text
id
user_id
asset_type
variant
storage_provider
storage_key
content_type
size_bytes
expires_at
used_at
created_at
```

## 不引入统一 file_assets 表

本轮先在现有领域表上增加必要字段，避免一次性重构过大。

未来当头像、路线封面、轨迹文件、活动轨迹和更多媒体资产需要统一审计、清理、权限和生命周期管理时，再考虑新增统一 `file_assets` 表并写 ADR。
