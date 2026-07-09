# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes for this slice.

## 交付内容

- 新增 `RoutePlanSnapshot` ORM 模型与 `route_plan_snapshots` 表（含 `UniqueConstraint(source_candidate_id)`）。
- 新增快照相关 Pydantic Schema：`RoutePlanSnapshotItem` / `RoutePlanSnapshotListResponse` / `RoutePlanSnapshotDetailResponse`。
- 新增 3 个接口：`POST .../candidate-routes/{candidate_id}/save`、`GET /api/my/route-plan-snapshots`、`GET /api/my/route-plan-snapshots/{snapshot_id}`。
- 保存逻辑复制候选当时的 route_summary / planning_detail / evidence / advantage_tags / score_breakdown / recommendation_reason。
- 新增快照 API 测试 `backend/tests/trip_plans/test_route_plan_snapshots_api.py`。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test_iter5_tmp.db'; pytest backend/tests/trip_plans/test_route_plan_snapshots_api.py -v
```

```text
历史迭代，未记录具体通过数；当前测试文件含 5 个用例（保存创建、重复保存拒绝、列表仅当前用户、详情返回快照内容、禁止跨用户访问）。
```

## 遗留风险

- 列表暂不支持分页、status / keyword 查询；数据量增长后需补。
- 不保存 user_note / share_text / actions，相关能力待后续迭代。
- evidence 为保存时刻复制，不自动刷新天气 / 交通 / 路况，存在过期风险（用户需自行核实）。
- snapshot.route 为保存时复制的 route_summary，与 route_asset 后续内容可能不一致；route_id 仍指向原 route_asset 以便进入线路本体详情。

## 对齐与决策

### 历史迭代

- 点击候选详情不创建 snapshot；只有点击保存才创建 snapshot（由 save 接口触发）。
- snapshot 内容为保存时刻复制，不随 route_asset 后续变化自动变化。
- snapshot.route.route_id 仍指向原 route_asset，可进入线路本体详情。
- snapshot.planning_detail / evidence 为保存时复制的候选详情内容。
- 详情可通过 continue_trip_plan_id 回到来源 TripPlan 继续对话。
- 同一 candidate 只能保存一次（UniqueConstraint）。

> 调查/对齐记录：本轮为历史已交付迭代，原始对齐讨论未记录；上述决策从现有代码与文档还原。
