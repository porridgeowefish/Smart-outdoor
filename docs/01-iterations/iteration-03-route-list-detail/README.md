# Iteration 03 Route List + Detail

Status: superseded (API 已被 Iteration 07 超越；本轮交付仍为历史事实源)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this iteration directory as the historical delivery boundary; current route APIs live in backend code.

## 用户闭环

用户在线路 Tab 查看线路列表，点击线路卡片进入详情，并获得地图渲染所需 GeoJSON。

## 本轮目标

```text
提供线路列表查询（可见性 + 关键词 + 标签 + 指标范围筛选）。
提供线路详情查询（元数据 + 分析指标 + 轨迹 + 文件 + UI 能力标志）。
提供标签 taxonomy，供前端标签选择器使用。
```

## 范围

### 本轮覆盖

```text
GET /api/routes（列表 + 筛选 + 分页）
GET /api/routes/tag-taxonomy
GET /api/routes/{route_id}（详情）
public + 当前用户 private 可见性校验
列表返回 location、track_preview、display_tags
详情返回 analysis、track、primary_file、actions
```

### 暂不进入

```text
不交付下载 API。
不交付编辑 API。
不交付 send-to-trip-plan API（actions 标志存在，但接口本轮不实现）。
不调用 Agent、天气或交通。
不生成 trip plan snapshot。
```

## 历史来源

- [MVP_IMPLEMENTATION_SLICES.md](../../99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md)
- [US-03_ROUTE_MODULE_DESIGN.md](../../99-archive/backend-docs-legacy/US-03_ROUTE_MODULE_DESIGN.md)
- [iteration-07 README](../iteration-07-high-fidelity-track-preview/README.md)（超越本轮 track 契约）
