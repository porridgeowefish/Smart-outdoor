# Iteration 03 Route List + Detail

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以在线路 Tab 查看线路列表，点击线路卡片进入详情，并获得地图渲染所需 GeoJSON。

## 范围

接口：

```text
GET /api/routes
GET /api/routes/tag-taxonomy
GET /api/routes/{route_id}
```

交付：

```text
public + 当前用户 private 可见性
标签筛选
标签 taxonomy
线路详情
analysis 返回
location 返回
track_preview 返回
track.geojson 返回
primary_file 返回
权限校验
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md`

## 本轮必补文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```
