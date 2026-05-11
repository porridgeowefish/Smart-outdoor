# Iteration 02 Route Upload + Parser

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以上传 GPX / KML / GeoJSON，系统保存原始文件，解析轨迹并生成线路资产。

## 范围

接口：

```text
POST /api/routes/upload
```

核心对象：

```text
route_assets
route_files
route_analysis_snapshots
```

交付：

```text
合法文件类型校验
轨迹解析
track_geojson 生成
manual_tags 保存
parse_status 成功/失败处理
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md`
- `docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md`

## 本轮必补文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

