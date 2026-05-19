# 50 领域边界

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: key domain boundaries for routes, tracks, and rendering.

## 读取入口

```text
docs/00-product-and-architecture/DOMAIN_MODEL.md
docs/00-product-and-architecture/DATA_MODEL.md
当前迭代 DATABASE_DESIGN.md
ORM model、迁移或初始化脚本
```

## route_asset 与 activity_track

```text
route_asset 是线路资产，用于线路库、搜索、规划、Agent 推荐。
activity_track 是用户已完成活动，用于能力画像。
二者不能混用。
用户上传想规划的线路，不等于用户已经完成过这条线路。
```

## 原始轨迹与渲染轨迹

```text
原始 KML / GPX / GeoJSON 必须保存为文件资产。
前端渲染使用解析后的简化 track_geojson。
前端地图优先使用 track_geojson，不要直接解析原始 KML/GPX。
```
