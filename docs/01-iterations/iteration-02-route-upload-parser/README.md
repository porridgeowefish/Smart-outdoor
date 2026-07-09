# Iteration 02 Route Upload + Parser

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation plus this iteration directory; current upload contract is Iteration 07.

> Superseded by Iteration 07: 上传接口的 multipart 文件上传契约在 Iteration 07 被替换为 JSON metadata complete。本文保留 Iteration 02 历史交付边界。

## 用户闭环

用户上传 GPX / KML / GeoJSON 轨迹文件，系统保存原始文件、解析轨迹并生成线路资产，以便后续线路展示和 Agent 推荐使用。

## 本轮目标

```text
合法文件类型校验。
轨迹解析：距离、爬升、起终点、track_geojson。
生成 route_asset / route_file / route_analysis_snapshot。
解析失败保留资产与文件，标记 parse_status=failed。
```

## 范围

### 本轮覆盖

```text
POST /api/routes/upload（multipart 形态，已被 iter07 取代）。
route_assets / route_files / route_analysis_snapshots 三张表。
GPX / KML / GeoJSON 解析。
可选封面图上传。
manual_tags 保存。
parse_status 成功 / 失败处理。
```

### 暂不进入

```text
不做线路列表查询、详情、可见性过滤（后续迭代）。
不做标签体系标准化（iter 后续）。
不做对象存储 / 前端直传（iter07）。
```

## 历史来源

- [MVP_IMPLEMENTATION_SLICES.md](../../99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md)
- [US-03_ROUTE_MODULE_DESIGN.md](../../99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md)
- [US-01_DATABASE_DESIGN.md](../../99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md)
- [iteration-07](../iteration-07-object-storage-image-assets/README.md)（取代本轮上传契约）
