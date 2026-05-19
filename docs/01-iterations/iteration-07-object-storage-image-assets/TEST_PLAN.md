# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: backend tests after implementation.

## StorageService 单元测试

```text
local provider 可以根据 storage_key 生成 public URL。
local provider 可以读取 storage_key 对应 bytes。
local provider 可以写入 full track_geojson 派生文件。
object storage provider 可以通过 mock client 验证临时凭据生成参数。
COS provider 可以通过 mock client 验证临时凭据生成参数。
StorageService 读取不存在对象时返回 STORAGE_OBJECT_NOT_FOUND。
```

## 上传凭据测试

```text
未登录不能申请上传凭据。
avatar 凭据只能生成 users/{user_id}/avatar/ 前缀 key。
route_cover 凭据只能生成当前用户可用的 route cover 前缀 key。
route_track_raw 凭据只允许 GPX / KML / GeoJSON content_type 或扩展名。
凭据包含 expires_at。
非法 asset_type 返回 400。
```

## 图片 metadata 测试

```text
PATCH /api/me 接收 avatar display / thumbnail metadata。
PATCH /api/me 写入 avatar_url、avatar_storage_key、avatar_variants、avatar_original_filename、avatar_processing_status=ready。
PATCH /api/me 不接收图片原图。
POST /api/routes/upload 接收 cover large / thumbnail metadata。
POST /api/routes/upload 写入 cover_image_url、cover_storage_key、cover_image_variants、cover_original_filename、cover_processing_status=ready。
metadata storage_key 不属于当前用户时返回 INVALID_STORAGE_OBJECT。
```

## 路线轨迹文件测试

```text
POST /api/routes/upload 接收 JSON metadata，不再接收 multipart 文件。
旧 multipart 请求不再作为成功路径；兼容期策略为直接替换。
后端根据 track_file.storage_key 读取原始 bytes。
checksum 基于对象存储中的原始 bytes 计算。
route_files 写入 storage_provider、storage_key、content_type、original_filename、file_size_bytes、checksum。
解析失败仍保留 route_file，并标记 parse_status=failed。
```

## 派生 GeoJSON 测试

```text
后端解析 raw track 后生成 full track_geojson。
full track_geojson 写入 StorageService，数据库保存 track_geojson_storage_key 和 track_geojson_url。
数据库保存 track_preview_geojson。
preview 使用 Douglas-Peucker。
preview_tolerance_m=10。
preview_max_segment_length_m=150。
preview 保留首尾点。
preview 不使用最多 80 点硬限制。
analysis_json 记录 preview_algorithm、preview_tolerance_m、preview_max_segment_length_m、preview_point_count、full_point_count。
```

## API 测试

```text
GET /api/routes 返回 thumbnail cover_image_url 和 track_preview。
GET /api/routes/{route_id} 返回 large cover_image_url、track_preview、track.track_url、primary_file.file_url。
GET /api/routes/{route_id}/track 校验权限后返回完整派生 GeoJSON。
其他用户 private route 的 /track 返回 404 ROUTE_NOT_FOUND。
primary_file.file_url 是原始轨迹文件 URL，不是地图渲染主路径。
未登录请求仍返回 401 UNAUTHORIZED。
```

## 契约测试

```text
/openapi.json 包含 upload-credentials、routes upload JSON complete 和 route track 接口。
前端生成类型不需要手写 Response 类型。
mock response 使用同一套 URL、storage_key、variants 和 track_preview 字段。
```

## Cloud Object Storage Smoke Test

```text
Any frontend direct-upload change must run a cloud/browser-equivalent smoke test.
FastAPI TestClient and the local storage provider are not enough to close the slice.

Required checks:
- COS bucket ACL is public-read when using naked public read URLs.
- COS Referer anti-hotlink allows only the deployed frontend origin and denies empty Referer.
- COS CORS rule exists for the deployed frontend origin.
- POST /api/storage/upload-credentials returns 200.
- OPTIONS signed PUT upload_url with Origin and Access-Control-Request-* headers returns 200.
- PUT signed upload_url with Origin, Referer, and Content-Type uploads a probe object.
- Avatar upload credentials and signed PUT upload a probe object.
- Naked COS cover URL returns 403 for empty Referer.
- Naked COS cover URL returns 403 for untrusted Referer.
- Naked COS cover URL returns 200 for allowed Referer.
- GET /api/routes/{route_id}/track returns 200 after upload/read configuration changes.

Reusable smoke script:
python scripts/verify_cloud_object_storage_smoke.py
```
