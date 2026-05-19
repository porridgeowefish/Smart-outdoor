# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-15
Source of truth: this iteration plus implementation tests after this slice lands.

## US-07.1 申请临时上传凭据

作为前端，我希望先向后端申请临时上传凭据，以便头像、路线封面和路线轨迹文件可以直传到存储服务，降低后端带宽和 CPU 压力。

验收要点：

```text
后端提供 POST /api/storage/upload-credentials。
凭据绑定当前用户、asset_type、variant、content_type 和 key 前缀。
前端不能任意写入不属于自己的 storage_key。
凭据有过期时间。
local provider 和 object storage provider 使用相同业务契约。
```

## US-07.2 头像 URL 化与图片版本

作为登录用户，我希望上传头像后，前端拿到稳定可访问的头像 URL，以便在本地和云部署环境中都能正常展示。

验收要点：

```text
前端本地压缩头像并生成 display / thumbnail。
前端用临时凭据直传两个处理后版本。
PATCH /api/me 接收 avatar_variants metadata 并写入 users。
上传图片原图不发送给后端，也不长期保存。
用户资料响应返回 avatar_url，且 avatar_url = avatar_variants.display.url。
```

## US-07.3 路线封面 URL 化与图片版本

作为线路上传者，我希望路线封面由前端压缩并直传，线路列表和详情都能使用合适尺寸的封面 URL。

验收要点：

```text
前端本地压缩路线封面并生成 large / thumbnail。
前端用临时凭据直传两个处理后版本。
POST /api/routes/upload 接收 cover_image_variants metadata。
上传图片原图不发送给后端，也不长期保存。
GET /api/routes 默认返回 thumbnail URL。
GET /api/routes/{route_id} 默认返回 large URL。
```

## US-07.4 轨迹文件直传与后端解析

作为线路上传者，我希望路线原始轨迹文件直传存储服务，同时后端仍能解析出稳定的线路指标和渲染数据。

验收要点：

```text
前端用临时凭据直传 GPX / KML / GeoJSON 原始文件。
轨迹文件不压缩、不改写语义内容。
POST /api/routes/upload 接收已上传轨迹文件 metadata。
后端根据 storage_key 读取原始 bytes。
后端基于原始 bytes 计算 checksum。
后端解析并写入 distance、elevation、bounds、center_point 等指标。
```

## US-07.5 高保真 preview 与完整派生轨迹

作为移动端用户，我希望线路列表和详情初屏快速展示可信路线形状，同时在详情地图中可以按需加载完整轨迹。

验收要点：

```text
full track_geojson 作为派生文件存储到对象存储。
track_preview_geojson 存数据库，用于列表和详情初屏。
preview 使用 Douglas-Peucker 高保真简化。
preview_tolerance_m = 10。
preview_max_segment_length_m = 150。
preview 不使用最多 80 点硬限制。
原始 GPX / KML 不作为前端地图渲染主路径。
```

## US-07.6 为异步处理预留状态

作为维护者，我希望数据库能表达图片处理状态，以便后续从前端同步直传平滑迁移到队列或云函数处理。

验收要点：

```text
users 保留 avatar_processing_status。
route_assets 保留 cover_processing_status。
本轮前端处理并直传成功后写 ready。
metadata 校验失败写 failed 或返回错误。
本轮不引入消息队列和真实云函数触发。
```
