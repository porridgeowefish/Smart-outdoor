# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM models and migrations after implementation.

## 表

```text
复用 users（新增头像存储字段）。
复用 route_assets（新增封面存储字段）。
复用 route_files（新增对象存储字段）。
复用 route_analysis_snapshots（新增 preview 与 full track 存储字段）。
不新增统一 file_assets 表。
本轮不新增 storage_upload_intents 持久化表（凭据由 provider 生成并带过期时间）。
```

## users

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| avatar_url | str\|null | String(500) | `= avatar_variants.display.url` | 复用 |
| avatar_storage_provider | str\|null | String(32)，`local`/`cos`/`object_storage` | nullable | 新增 |
| avatar_storage_key | str\|null | String(500)，`users/{user_id}/avatar/...` | `= avatar_variants.display.storage_key` | 新增 |
| avatar_variants | object | `{display: {storage_key:str, url:str, width:int\|null, height:int\|null, content_type:str, size_bytes:int}, thumbnail: {...}}` | JSON | 新增 |
| avatar_original_filename | str\|null | String(255)，仅文件名文本 | nullable，不存原图 | 新增 |
| avatar_processing_status | str\|null | String(32)，本轮 `ready`/`failed` | nullable | 新增 |

```json
{
  "display": {
    "storage_key": "users/user_1/avatar/display-<token>.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/display-<token>.webp",
    "width": 512,
    "height": 512,
    "content_type": "image/webp",
    "size_bytes": 123456
  },
  "thumbnail": {
    "storage_key": "users/user_1/avatar/thumbnail-<token>.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/thumbnail-<token>.webp",
    "width": 128,
    "height": 128,
    "content_type": "image/webp",
    "size_bytes": 30000
  }
}
```

不新增 `avatar_original_url` / `avatar_original_storage_key` / `avatar_content_type` / `avatar_size_bytes`；`content_type` 和 `size_bytes` 放在每个 variant 内部。

## route_assets

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| cover_image_url | str\|null | String(500) | `= cover_image_variants.large.url` | 复用 |
| cover_storage_provider | str\|null | String(32)，`local`/`cos`/`object_storage` | nullable | 新增 |
| cover_storage_key | str\|null | String(500)，`users/{user_id}/routes/covers/...` | `= cover_image_variants.large.storage_key` | 新增 |
| cover_image_variants | object | `{large: {storage_key:str, url:str, width:int\|null, height:int\|null, content_type:str, size_bytes:int}, thumbnail: {...}}` | JSON | 新增 |
| cover_original_filename | str\|null | String(255)，仅文件名文本 | nullable，不存原图 | 新增 |
| cover_processing_status | str\|null | String(32)，本轮 `ready`/`failed` | nullable | 新增 |

```json
{
  "large": {
    "storage_key": "routes/route_1/cover/large-<token>.webp",
    "url": "https://cdn.example.com/routes/route_1/cover/large-<token>.webp",
    "width": 1280,
    "height": 720,
    "content_type": "image/webp",
    "size_bytes": 450000
  },
  "thumbnail": {
    "storage_key": "routes/route_1/cover/thumbnail-<token>.webp",
    "url": "https://cdn.example.com/routes/route_1/cover/thumbnail-<token>.webp",
    "width": 480,
    "height": 270,
    "content_type": "image/webp",
    "size_bytes": 100000
  }
}
```

列表页优先使用 `cover_image_variants.thumbnail.url`；详情页使用 `cover_image_url`/`large.url`。不新增 `cover_original_url` 等独立原图字段。

## route_files

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| file_url | str | String(500) | 原始轨迹文件可访问 URL | 复用 |
| file_type | str | String(32)，`gpx`/`kml`/`geojson` | — | 复用 |
| file_size_bytes | int\|null | Integer | 原始文件大小 | 复用 |
| checksum | str\|null | String(64)，SHA-256 | 后端读取对象存储 bytes 后计算 | 复用 |
| parse_status | str | String(32)，`pending`/`parsed`/`failed` | 解析状态 | 复用 |
| parse_error | str\|null | Text | 解析失败原因（如 `TRACK_PARSE_FAILED`） | 复用 |
| storage_provider | str\|null | String(32)，`local`/`cos`/`object_storage` | nullable | 新增 |
| storage_key | str\|null | String(500)，`users/{user_id}/routes/raw/...` | 后端读取/下载/删除依据 | 新增 |
| content_type | str\|null | String(120)，上传对象 MIME | nullable | 新增 |
| original_filename | str\|null | String(255)，用户上传原始文件名 | nullable | 新增 |

轨迹文件不做 variants、不做 processing_status。

## route_analysis_snapshots

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| track_geojson | object | JSON，LineString GeoJSON | legacy 兼容字段，新数据不再写 full | 复用（废弃写入） |
| analysis_json | object | JSON，含 preview metadata（见下） | 扩展分析数据 | 复用（扩展） |
| track_preview_geojson | object\|null | JSON，高保真简化 LineString | 用于列表和详情初屏 | 新增 |
| track_preview_point_count | int\|null | Integer | preview 点数 | 新增 |
| track_geojson_storage_provider | str\|null | String(32) | full 派生 GeoJSON 所在 provider | 新增 |
| track_geojson_storage_key | str\|null | String(500)，`users/{user_id}/routes/derived/...` | 指向对象存储中的 full GeoJSON | 新增 |
| track_geojson_url | str\|null | String(500) | full 派生 GeoJSON 可访问/受控 URL | 新增 |
| track_geojson_point_count | int\|null | Integer | full GeoJSON 点数 | 新增 |
| track_geojson_size_bytes | int\|null | Integer | full GeoJSON 文件大小 | 新增 |

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

preview 算法参数：Douglas-Peucker 高保真简化，`tolerance_m=10`，`max_segment_length_m=150`，保留首尾点，不使用最多 80 点硬限制。

## 约束

```text
storage_key 必须归属当前用户（users/{user_id}/ 前缀）；后端校验。
storage_key 不可含绝对路径前缀或 ..；后端校验。
avatar_url = avatar_variants.display.url；cover_image_url = cover_image_variants.large.url。
checksum 由后端读取对象存储原始 bytes 后计算 SHA-256。
轨迹解析失败时，route_asset 与 route_file 记录仍保留，parse_status=failed。
```

## 迁移与同步点

```text
新增头像/封面/轨迹/分析存储相关字段（含 JSON variants）。
PATCH /api/me：写 avatar_* 字段并校验 storage_key 归属。
POST /api/routes/upload：写 route_files.*、route_assets.cover_* 与 route_analysis_snapshots.* 新字段。
GET /api/routes：读取 cover_image_variants.thumbnail.url 与 track_preview_geojson。
GET /api/routes/{route_id}：读取 large 封面、track_preview_geojson、track.track_url。
GET /api/routes/{route_id}/track：读取 track_geojson_storage_key 对应对象。
旧 track_geojson 字段保留为 legacy 兼容字段，新数据不写 full。
```

## 历史来源

- [DATA_MODEL.md](../../00-product-and-architecture/DATA_MODEL.md)
- [API_CONTRACT.md](./API_CONTRACT.md)
- backend/app/features/users/model.py、routes/model.py、storage/service.py、storage/schemas.py、routes/schemas.py
