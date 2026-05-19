# Acceptance Criteria

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: product acceptance and implementation tests.

```text
存在统一 StorageService，业务代码不直接拼接本地文件路径作为存储契约。
local provider 可用于本地开发。
object storage provider 可通过配置启用或至少有 mockable 边界。
云端对象存储 provider 优先支持腾讯云 COS。
存在 POST /api/storage/upload-credentials。
图片和轨迹文件都支持前端直传。
后端不接收图片原图。
头像 metadata 入库后返回 avatar_url。
头像保存 display / thumbnail variants。
路线封面保存 large / thumbnail variants。
线路列表使用 thumbnail cover URL。
线路详情使用 large cover URL。
路线原始 GPX / KML / GeoJSON 完整保存。
route_files 记录 storage_provider、storage_key、content_type、size_bytes、original_filename、checksum。
checksum 由后端读取对象存储原始 bytes 后计算。
POST /api/routes/upload 使用 JSON metadata complete，不再依赖 multipart 文件流。
旧 multipart 上传契约被直接替换，不保留并行 legacy 上传接口。
full track_geojson 作为派生文件写入对象存储。
track_preview_geojson 写入数据库。
preview 使用 Douglas-Peucker，tolerance_m=10，max_segment_length_m=150。
preview 不使用最多 80 点硬限制。
GET /api/routes 返回 track_preview。
GET /api/routes/{route_id} 返回 track_preview 和完整轨迹访问入口。
GET /api/routes/{route_id}/track 返回完整派生 GeoJSON 或受控访问入口。
原始轨迹 file_url 不作为地图渲染主路径。
前端页面不关心 local / object storage provider。
mock / real storage 切换不改页面代码。
```

## 明确不做

```text
不保留图片上传原图。
不压缩或改写轨迹原始文件。
不把 full track_geojson 继续作为数据库主事实源。
不一次性新增统一 file_assets 表。
不在本轮实现完整文件管理后台。
不在本轮引入消息队列或真实云函数触发。
```
