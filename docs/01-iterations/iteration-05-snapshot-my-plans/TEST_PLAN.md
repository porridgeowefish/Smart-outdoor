# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests.

## Service / Unit

- [US-05.1] 保存候选 → 创建 route_plan_snapshot 并复制候选 route_summary / planning_detail / evidence / advantage_tags / score_breakdown / recommendation_reason。
- 保存后 route_asset 变化不影响已保存 snapshot 的内容。
- 保存接口当前不接收也不保存 user_note。

## API

- [US-05.1] 登录用户保存存在的候选 → 返回 201 与快照详情。
- [US-05.1] 重复保存同一 candidate → 返回 409 ROUTE_PLAN_SNAPSHOT_EXISTS。
- [US-05.2] 我的规划列表只返回当前用户的 snapshot。
- [US-05.2] 列表响应返回 total 与 items。
- [US-05.3] 详情返回保存时刻 route_summary / planning_detail / evidence。
- [US-05.3] 详情返回 continue_trip_plan_id。

## 权限

- 未登录访问任意接口 → 返回 401。
- 其他用户访问别人的 snapshot 详情 → 返回 404 ROUTE_PLAN_SNAPSHOT_NOT_FOUND。

## 失败路径

- 保存不存在的候选 → 返回 404 CANDIDATE_ROUTE_NOT_FOUND。
- 详情查询不存在的 snapshot_id → 返回 404 ROUTE_PLAN_SNAPSHOT_NOT_FOUND。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test_iter5_tmp.db'; pytest backend/tests/trip_plans/test_route_plan_snapshots_api.py -v
```
