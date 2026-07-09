# API Contract

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json` after implementation.

## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|
| POST | `/api/storage/upload-credentials` | 新增：生成前端直传用的临时上传凭据 |
| PATCH | `/api/me` | 新增可写 `avatar`（ImageAssetMetadata）；响应含 `avatar_url` 等头像字段 |
| POST | `/api/routes/upload` | 从 multipart 文件上传改为 JSON metadata complete；接收已直传轨迹/封面 metadata |
| GET | `/api/routes` | 响应 `cover_image_url` 改为 thumbnail；新增 `track_preview` |
| GET | `/api/routes/{route_id}` | 响应新增 `track_preview`、`track.track_url`、`primary_file` |
| GET | `/api/routes/{route_id}/track` | 新增：返回完整派生 full track_geojson |

> Superseded by iter-07：旧 `POST /api/routes/upload` 的 multipart/form-data 契约被本轮直接替换，不保留并行 legacy 上传接口。

## 请求 / 响应示例

### POST /api/storage/upload-credentials

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
  "storage_key": "users/user_1/avatar/display-<token>.webp",
  "upload_url": "https://storage.example.com/upload-signed-url",
  "public_url": "https://cdn.example.com/users/user_1/avatar/display-<token>.webp",
  "headers": {
    "Content-Type": "image/webp"
  },
  "expires_at": "2026-05-15T12:00:00Z"
}
```

local provider 的 `upload_url` 形如 `/api/storage/local-upload?key=...`（后端兼容上传入口），凭据契约与云 provider 一致。

### PATCH /api/me

用途：更新当前用户资料，并保存头像处理后版本 metadata。

Request:

```json
{
  "nickname": "Demo",
  "avatar": {
    "storage_provider": "object_storage",
    "storage_key": "users/user_1/avatar/display-<token>.webp",
    "url": "https://cdn.example.com/users/user_1/avatar/display-<token>.webp",
    "original_filename": "avatar.jpg",
    "processing_status": "ready",
    "variants": {
      "display": {
        "storage_key": "users/user_1/avatar/display-<token>.webp",
        "url": "https://cdn.example.com/users/user_1/avatar/display-<token>.webp",
        "width": 512,
        "height": 512,
        "content_type": "image/webp",
        "size_bytes": 120000
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
  }
}
```

Response 关键字段：

```json
{
  "id": "user_1",
  "username": "demo",
  "nickname": "Demo",
  "avatar_url": "https://cdn.example.com/users/user_1/avatar/display-<token>.webp",
  "avatar_storage_provider": "object_storage",
  "avatar_storage_key": "users/user_1/avatar/display-<token>.webp",
  "avatar_variants": { "...": "见 request.variants" },
  "avatar_processing_status": "ready"
}
```

### POST /api/routes/upload

用途：路线上传 complete。真实文件已由前端直传，本接口接收 metadata，完成数据库入库、轨迹读取和解析。

Request:

```json
{
  "name": "Demo Route",
  "description": "周末轻徒步",
  "visibility": "public",
  "manual_tags": {
    "地形": ["山地"]
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
    "storage_key": "routes/route_tmp/cover/large-<token>.webp",
    "url": "https://cdn.example.com/routes/route_tmp/cover/large-<token>.webp",
    "original_filename": "cover.jpg",
    "processing_status": "ready",
    "variants": {
      "large": {
        "storage_key": "routes/route_tmp/cover/large-<token>.webp",
        "url": "https://cdn.example.com/routes/route_tmp/cover/large-<token>.webp",
        "width": 1280,
        "height": 720,
        "content_type": "image/webp",
        "size_bytes": 450000
      },
      "thumbnail": {
        "storage_key": "routes/route_tmp/cover/thumbnail-<token>.webp",
        "url": "https://cdn.example.com/routes/route_tmp/cover/thumbnail-<token>.webp",
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

### GET /api/routes

用途：线路列表。

Response 关键字段：

```json
{
  "items": [
    {
      "route_id": "route_1",
      "name": "Demo Route",
      "cover_image_url": "https://cdn.example.com/routes/route_1/cover/thumbnail-<token>.webp",
      "location": "成都",
      "visibility": "public",
      "distance_km": 15.2,
      "elevation_gain_m": 860.0,
      "manual_tags": { "...": "..." },
      "display_tags": ["山地"],
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
  ],
  "pagination": { "page": 1, "page_size": 20, "total": 1 }
}
```

### GET /api/routes/{route_id}

用途：线路详情初始数据。

Response 关键字段：

```json
{
  "route_id": "route_1",
  "name": "Demo Route",
  "cover_image_url": "https://cdn.example.com/routes/route_1/cover/large-<token>.webp",
  "track_preview": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "point_count": 420,
    "geojson": { "type": "LineString", "coordinates": [[104.0, 30.0]] }
  },
  "track": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "source": "derived_full_geojson",
    "point_count": 12840,
    "track_url": "/api/routes/route_1/track",
    "geojson": null
  },
  "primary_file": {
    "file_id": "file_1",
    "file_type": "gpx",
    "file_url": "https://cdn.example.com/routes/user_1/uploads/demo.gpx",
    "parse_status": "parsed"
  }
}
```

### GET /api/routes/{route_id}/track

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

后端先校验 route 可见性，再从 `track_geojson_storage_key` 读取派生 GeoJSON。后续如文件过大，可改为返回短期 signed URL，但前端仍通过本接口取得受控访问入口。

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 401 | UNAUTHORIZED | 未登录访问受保护接口 |
| 400 | UNSUPPORTED_FILE_TYPE | 轨迹文件非 GPX/KML/GeoJSON |
| 400 | UNSUPPORTED_COVER_IMAGE_TYPE | 封面图非 JPEG/PNG/WebP |
| 400 | INVALID_MANUAL_TAGS | manual_tags 不是合法 JSON 对象 |
| 400 | INVALID_STORAGE_OBJECT | storage metadata/key 不合法或不属于当前用户 |
| 400 | STORAGE_OBJECT_NOT_FOUND | storage_key 对应对象不存在（读取/解析时） |
| 400 | TRACK_PARSE_FAILED | 活动轨迹解析失败（parse_error 落库，资产/文件记录保留） |
| 404 | ROUTE_NOT_FOUND | 路线不存在或对当前用户不可见 |
| 503 | STORAGE_PROVIDER_NOT_CONFIGURED | 云 provider 凭据缺失或 SDK 不可用 |

## 历史来源

- [API_CONTRACT_STRATEGY.md](../../00-product-and-architecture/API_CONTRACT_STRATEGY.md)
- [DATABASE_DESIGN.md](./DATABASE_DESIGN.md)
- [DELIVERY_NOTES.md](./DELIVERY_NOTES.md)
