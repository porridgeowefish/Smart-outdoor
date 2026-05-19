# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: Pydantic V2 schemas and `/openapi.json` after implementation.

## 本轮接口策略

Iteration 07 将文件上传改为两阶段：

```text
阶段 A：前端向后端申请临时上传凭据。
阶段 B：前端直传文件后，把 url、storage_key 和 variants metadata 提交给业务接口 complete。
```

旧的 `POST /api/routes/upload multipart/form-data` 契约被本轮直接替换，不保留并行 legacy 上传接口。

新增或改造接口：

```text
POST /api/storage/upload-credentials
PATCH /api/me
POST /api/routes/upload
GET /api/routes
GET /api/routes/{route_id}
GET /api/routes/{route_id}/track
```

## POST /api/storage/upload-credentials

用途：生成前端直传使用的临时上传凭据。

Request:

```json
{
  "asset_type": "avatar",
  "variant": "display",
  "content_type": "image/webp",
  "original_filename": "avatar.webp",
  "size_bytes": 120000
}
```

`asset_type` 取值：

```text
avatar
route_cover
route_track_raw
route_track_geojson
```

Response:

```json
{
  "storage_provider": "cos",
  "storage_key": "users/user_1/avatar/display.webp",
  "upload_url": "https://storage.example.com/upload-signed-url",
  "public_url": "https://cdn.example.com/users/user_1/avatar/display.webp",
  "headers": {
    "Content-Type": "image/webp"
  },
  "expires_at": "2026-05-15T12:00:00Z"
}
```

规则：

```text
后端必须限制 storage_key 前缀归属。
凭据必须有过期时间。
前端不能用头像凭据上传路线文件。
local provider 可以返回本地等价 upload_url 或后端兼容上传入口。
云端 provider 优先使用腾讯云 COS。
```

## PATCH /api/me

用途：更新当前用户资料，并保存头像处理后版本 metadata。

Request:

```json
{
  "nickname": "Demo",
  "bio": "喜欢轻徒步",
  "avatar": {
    "storage_provider": "object_storage",
    "storage_key": "users/user_1/avatar/display.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/display.webp",
    "original_filename": "avatar.jpg",
    "processing_status": "ready",
    "variants": {
      "display": {
        "storage_key": "users/user_1/avatar/display.webp",
        "url": "https://cdn.example.com/users/user_1/avatar/display.webp",
        "width": 512,
        "height": 512,
        "content_type": "image/webp",
        "size_bytes": 120000
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
  }
}
```

Response 关键字段：

```json
{
  "id": "user_1",
  "username": "demo",
  "nickname": "Demo",
  "avatar_url": "https://cdn.example.com/users/user_1/avatar/display.webp"
}
```

规则：

```text
avatar_url = avatar_variants.display.url。
avatar_storage_key = avatar_variants.display.storage_key。
后端不接收图片原图。
后端保存 variants metadata 并校验 key 归属。
```

## POST /api/routes/upload

用途：路线上传 complete。真实文件已由前端直传，本接口接收 metadata，完成数据库入库、轨迹读取和解析。

Request:

```json
{
  "name": "Demo Route",
  "description": "周末轻徒步",
  "visibility": "public",
  "manual_tags": {
    "scenery": ["森林"]
  },
  "track_file": {
    "storage_provider": "object_storage",
    "storage_key": "routes/user_1/uploads/demo.gpx",
    "file_url": "https://cdn.example.com/routes/user_1/uploads/demo.gpx",
    "file_type": "gpx",
    "content_type": "application/gpx+xml",
    "size_bytes": 123456,
    "original_filename": "demo.gpx"
  },
  "cover_image": {
    "storage_provider": "object_storage",
    "storage_key": "routes/route_tmp/cover/large.webp",
    "url": "https://cdn.example.com/routes/route_tmp/cover/large.webp",
    "original_filename": "cover.jpg",
    "processing_status": "ready",
    "variants": {
      "large": {
        "storage_key": "routes/route_tmp/cover/large.webp",
        "url": "https://cdn.example.com/routes/route_tmp/cover/large.webp",
        "width": 1280,
        "height": 720,
        "content_type": "image/webp",
        "size_bytes": 450000
      },
      "thumbnail": {
        "storage_key": "routes/route_tmp/cover/thumbnail.webp",
        "url": "https://cdn.example.com/routes/route_tmp/cover/thumbnail.webp",
        "width": 480,
        "height": 270,
        "content_type": "image/webp",
        "size_bytes": 100000
      }
    }
  }
}
```

Response:

```json
{
  "route_id": "route_1",
  "file_id": "file_1",
  "parse_status": "parsed",
  "parse_error": null
}
```

规则：

```text
后端用 track_file.storage_key 读取对象存储中的原始 bytes。
checksum 由后端基于原始 bytes 计算。
后端解析生成 route_analysis_snapshots。
后端生成 full track_geojson 派生文件并写入 StorageService。
后端生成 track_preview_geojson 并写入数据库。
封面图片只保存前端上传后的 large / thumbnail metadata。
```

## GET /api/routes

用途：线路列表。

Response 关键字段：

```json
{
  "items": [
    {
      "route_id": "route_1",
      "name": "Demo Route",
      "cover_image_url": "https://cdn.example.com/routes/route_1/cover/thumbnail.webp",
      "distance_km": 15.2,
      "elevation_gain_m": 860.0,
      "track_preview": {
        "format": "geojson",
        "coordinate_system": "wgs84",
        "point_count": 420,
        "geojson": {
          "type": "LineString",
          "coordinates": [[104.0, 30.0], [104.001, 30.001]]
        }
      }
    }
  ]
}
```

规则：

```text
cover_image_url 默认返回 thumbnail URL。
track_preview 来自数据库 track_preview_geojson。
track_preview 不使用最多 80 点硬限制。
```

## GET /api/routes/{route_id}

用途：线路详情初始数据。

Response 关键字段：

```json
{
  "cover_image_url": "https://cdn.example.com/routes/route_1/cover/large.webp",
  "track_preview": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "point_count": 420,
    "geojson": {
      "type": "LineString",
      "coordinates": [[104.0, 30.0], [104.001, 30.001]]
    }
  },
  "track": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "source": "derived_full_geojson",
    "point_count": 12840,
    "track_url": "/api/routes/route_1/track"
  },
  "primary_file": {
    "file_id": "file_1",
    "file_type": "gpx",
    "file_url": "https://cdn.example.com/routes/user_1/uploads/demo.gpx",
    "parse_status": "parsed"
  }
}
```

规则：

```text
详情初屏使用 track_preview。
完整地图按需调用 GET /api/routes/{route_id}/track。
primary_file.file_url 是原始文件 URL，不作为地图渲染主路径。
```

## GET /api/routes/{route_id}/track

用途：获取完整派生 full track_geojson。

Response:

```json
{
  "format": "geojson",
  "coordinate_system": "wgs84",
  "source": "derived_full_geojson",
  "point_count": 12840,
  "geojson": {
    "type": "LineString",
    "coordinates": [[104.0, 30.0], [104.001, 30.001]]
  }
}
```

规则：

```text
后端先校验 route 可见性。
后端从 track_geojson_storage_key 读取派生 GeoJSON。
后续如文件过大，可改为返回短期 signed URL，但前端仍通过本接口取得受控访问入口。
```

## 错误码

```text
401 UNAUTHORIZED
400 UNSUPPORTED_FILE_TYPE
400 INVALID_MANUAL_TAGS
400 INVALID_STORAGE_OBJECT
400 STORAGE_OBJECT_NOT_FOUND
400 TRACK_PARSE_FAILED
404 ROUTE_NOT_FOUND
```
