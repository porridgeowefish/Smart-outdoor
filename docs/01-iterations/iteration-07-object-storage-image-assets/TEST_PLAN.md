# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests after implementation.

## Service / Unit

- [US-07.1] local provider 根据 storage_key 生成 public URL。
- [US-07.1] local provider 读取 storage_key 对应 bytes。
- [US-07.1] local provider 写入 full track_geojson 派生文件。
- [US-07.1] COS provider 通过 mock client 验证临时凭据生成参数。
- [US-07.1] StorageService 读取不存在对象 → STORAGE_OBJECT_NOT_FOUND。
- [US-07.1] storage_key 含 `..` 或绝对路径 → INVALID_STORAGE_OBJECT。
- [US-07.4] 后端根据 track_file.storage_key 读取原始 bytes。
- [US-07.4] checksum 基于对象存储原始 bytes 计算 SHA-256。
- [US-07.5] preview 使用 Douglas-Peucker，tolerance_m=10，max_segment_length_m=150。
- [US-07.5] preview 保留首尾点，不使用最多 80 点硬限制。
- [US-07.5] analysis_json 记录 preview_algorithm / preview_tolerance_m / preview_max_segment_length_m / preview_point_count / full_point_count。

## API

- [US-07.1] POST /api/storage/upload-credentials 返回 storage_provider / storage_key / upload_url / public_url / headers / expires_at。
- [US-07.1] avatar 凭据只生成 `users/{user_id}/avatar/` 前缀 key。
- [US-07.1] route_cover 凭据只生成 `users/{user_id}/routes/covers/` 前缀 key。
- [US-07.1] route_track_raw 凭据只允许 GPX/KML/GeoJSON content_type 或扩展名。
- [US-07.1] 非法 asset_type → 400 INVALID_STORAGE_OBJECT。
- [US-07.2] PATCH /api/me 接收 avatar display/thumbnail metadata，写 avatar_url/avatar_storage_key/avatar_variants/avatar_original_filename/avatar_processing_status=ready。
- [US-07.2] PATCH /api/me 不接收图片原图。
- [US-07.3] POST /api/routes/upload 接收 cover large/thumbnail metadata，写 cover_* 字段。
- [US-07.3] POST /api/routes/upload 写 cover_processing_status=ready。
- [US-07.4] POST /api/routes/upload 接收 JSON metadata，不再接收 multipart 文件。
- [US-07.4] route_files 写 storage_provider/storage_key/content_type/original_filename/file_size_bytes/checksum。
- [US-07.4] 解析失败仍保留 route_file，标记 parse_status=failed。
- [US-07.5] 后端解析 raw track 后生成 full track_geojson 并写入 StorageService。
- [US-07.5] 数据库保存 track_geojson_storage_key/track_geojson_url/track_preview_geojson。
- [US-07.5] GET /api/routes 返回 thumbnail cover_image_url 与 track_preview。
- [US-07.5] GET /api/routes/{route_id} 返回 large cover_image_url、track_preview、track.track_url、primary_file.file_url。
- [US-07.5] GET /api/routes/{route_id}/track 校验权限后返回完整派生 GeoJSON。
- [US-07.5] primary_file.file_url 是原始轨迹 URL，不是地图渲染主路径。
- [US-07.5] /openapi.json 包含 upload-credentials、routes upload JSON complete、route track 接口。
- [US-07.5] mock response 使用与真实响应同一套 URL/storage_key/variants/track_preview 字段。

## 权限

- 未登录申请上传凭据 → 401 UNAUTHORIZED。
- metadata storage_key 不属于当前用户 → 400 INVALID_STORAGE_OBJECT。
- 其他用户 private route 的 /track → 404 ROUTE_NOT_FOUND。
- 未登录访问受保护接口 → 401 UNAUTHORIZED。

## 失败路径

- storage_key 对应对象不存在 → 400 STORAGE_OBJECT_NOT_FOUND。
- 轨迹文件非 GPX/KML/GeoJSON → 400 UNSUPPORTED_FILE_TYPE。
- 封面图非 JPEG/PNG/WebP → 400 UNSUPPORTED_COVER_IMAGE_TYPE。
- manual_tags 非合法 JSON 对象 → 400 INVALID_MANUAL_TAGS。
- 云 provider 凭据缺失 / SDK 不可用 → 503 STORAGE_PROVIDER_NOT_CONFIGURED。

## 验证命令

```powershell
cd backend; python -m pytest
```

```powershell
python scripts/verify_cloud_object_storage_smoke.py
```

## 备注

Cloud Object Storage Smoke Test：任何前端直传改动必须跑一次云/浏览器等价冒烟，FastAPI TestClient 与 local provider 不足以闭环。必查项：

- COS bucket ACL 为 public-read（裸 URL 读时）。
- COS Referer 防盗链仅放行部署前端域名，Deny 空 Referer。
- COS 已配置面向部署前端域名的 CORS 规则。
- POST /api/storage/upload-credentials → 200。
- OPTIONS signed PUT upload_url（带 Origin / Access-Control-Request-\*）→ 200。
- PUT signed upload_url（带 Origin/Referer/Content-Type）上传探针对象 → 成功。
- 头像上传凭据 + signed PUT 上传探针对象 → 成功。
- 裸 COS cover URL：空 Referer → 403；非可信 Referer → 403；可信 Referer → 200。
- GET /api/routes/{route_id}/track → 200（上传/读取配置变更后回归）。

复用冒烟脚本：`scripts/verify_cloud_object_storage_smoke.py`。

## 历史来源

- [ACCEPTANCE_CRITERIA.md](./ACCEPTANCE_CRITERIA.md)
- [DELIVERY_NOTES.md](./DELIVERY_NOTES.md)
