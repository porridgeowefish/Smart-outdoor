# Iteration 07 Object Storage + Image Assets

Status: active
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: this iteration directory plus implementation after this slice lands.

## 用户闭环

用户上传头像、路线封面和路线原始轨迹文件时，前端先向后端申请临时上传凭据，再把文件直传到对象存储或本地等价存储。后端只保存可信 metadata、校验 storage key，并在路线 complete 阶段读取原始轨迹生成分析结果和派生 GeoJSON。

前端展示时只使用后端 API 返回的 URL、preview 轨迹或受控 track API，不关心文件在本地、对象存储还是 CDN 后面。

## 本轮目标

```text
引入统一 StorageService。
本地开发使用 local provider。
云部署使用 object storage provider，本轮优先接入腾讯云 COS。
新增临时上传凭据接口，支持前端直传。
图片由前端压缩并上传处理后版本，不保留上传原图。
路线原始轨迹文件 GPX / KML / GeoJSON 由前端直传，但必须完整保存和可追溯。
后端 complete 时读取轨迹 storage_key，计算 checksum，解析指标。
采用方案 C：数据库保存高保真 preview，完整派生 track_geojson 存对象存储。
```

## 范围

本轮覆盖：

```text
用户头像
路线封面
路线原始轨迹文件 GPX / KML / GeoJSON
路线派生 full track_geojson
路线 preview track_geojson
```

新增或改造接口：

```text
POST /api/storage/upload-credentials
PATCH /api/me
POST /api/routes/upload
GET /api/routes
GET /api/routes/{route_id}
GET /api/routes/{route_id}/track
```

说明：

```text
POST /api/routes/upload 从 multipart 文件上传改为 JSON metadata complete。
真实文件已经由前端通过临时凭据直传完成。
旧 multipart 契约直接替换，不保留并行 legacy 上传接口。
```

核心对象：

```text
users.avatar_url
users.avatar_variants
route_assets.cover_image_url
route_assets.cover_image_variants
route_files.file_url
route_files.storage_key
route_analysis_snapshots.track_preview_geojson
route_analysis_snapshots.track_geojson_storage_key
StorageService
Upload credentials
```

## 图片策略

```text
前端申请临时上传凭据。
前端压缩图片并生成目标版本。
头像上传 display / thumbnail。
路线封面上传 large / thumbnail。
后端保存 variants metadata。
后端不接收图片原图。
后端不长期保存图片原图。
processing_status 字段保留；本轮写入 ready / failed。
```

## 轨迹文件策略

```text
GPX / KML / GeoJSON 是原始数据资产。
前端使用临时凭据直传原始轨迹文件。
轨迹文件不压缩、不改写语义内容。
后端 complete 时读取 storage_key 对应 bytes。
checksum 由后端基于对象存储中的原始 bytes 计算。
后端解析轨迹并生成指标、full track_geojson 和 preview track_geojson。
```

## 轨迹渲染策略

```text
原始 GPX / KML / GeoJSON 不作为前端地图渲染主路径。
full track_geojson 是后端解析出的派生文件，存对象存储。
preview track_geojson 是数据库中的高保真轻量轨迹，用于列表和详情初屏。
GET /api/routes/{route_id}/track 返回完整派生 GeoJSON 或受控访问 URL。
```

preview 算法：

```text
Douglas-Peucker 高保真简化。
tolerance_m = 10。
max_segment_length_m = 150。
首尾点保留。
不使用最多 80 点硬限制。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- [API_CONTRACT_STRATEGY.md](../../00-product-and-architecture/API_CONTRACT_STRATEGY.md)
- [DATA_MODEL.md](../../00-product-and-architecture/DATA_MODEL.md)
- [iteration-01-auth-user](../iteration-01-auth-user/README.md)
- [iteration-02-route-upload-parser](../iteration-02-route-upload-parser/README.md)
- [iteration-03-route-list-detail](../iteration-03-route-list-detail/README.md)

## 本轮文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md
```
