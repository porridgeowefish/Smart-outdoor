# Iteration 07 Object Storage + Image Assets

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this iteration directory plus implementation after this slice lands.

## 用户闭环

用户上传头像、路线封面和路线原始轨迹文件时，前端先向后端申请临时上传凭据，再把文件直传到对象存储或本地等价存储。后端只保存可信 metadata、校验 storage key，并在路线 complete 阶段读取原始轨迹生成分析结果和派生 GeoJSON。前端展示时只使用后端 API 返回的 URL、preview 轨迹或受控 track API，不关心文件在本地、对象存储还是 CDN 后面。

## 本轮目标

```text
引入统一 StorageService。
本地开发使用 local provider；云部署使用腾讯云 COS provider。
新增临时上传凭据接口，支持前端直传。
图片由前端压缩并上传处理后版本，后端不保留上传原图。
路线原始轨迹文件（GPX/KML/GeoJSON）由前端直传，完整保存且可追溯。
后端 complete 时读取轨迹 storage_key，计算 checksum，解析指标。
方案 C：数据库保存高保真 preview，完整派生 track_geojson 存对象存储。
```

## 范围

### 本轮覆盖

```text
用户头像（display / thumbnail variants）。
路线封面（large / thumbnail variants）。
路线原始轨迹文件 GPX / KML / GeoJSON。
路线派生 full track_geojson（存对象存储）。
路线 preview track_geojson（存数据库）。
新增/改造接口：POST /api/storage/upload-credentials、PATCH /api/me、POST /api/routes/upload、GET /api/routes、GET /api/routes/{route_id}、GET /api/routes/{route_id}/track。
```

### 暂不进入

```text
不保留图片上传原图。
不压缩或改写轨迹原始文件。
不把 full track_geojson 继续作为数据库主事实源。
不一次性新增统一 file_assets 表。
不在本轮实现完整文件管理后台。
不在本轮引入消息队列或真实云函数触发。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- [API_CONTRACT_STRATEGY.md](../../00-product-and-architecture/API_CONTRACT_STRATEGY.md)
- [DATA_MODEL.md](../../00-product-and-architecture/DATA_MODEL.md)
- [iteration-01-auth-user](../iteration-01-auth-user/README.md)
- [iteration-02-route-upload-parser](../iteration-02-route-upload-parser/README.md)
- [iteration-03-route-list-detail](../iteration-03-route-list-detail/README.md)
