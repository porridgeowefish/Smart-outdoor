# Iteration 05 Snapshot / 我的规划

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以把候选线路保存到“我的规划”，之后查看快照列表和详情。

## 范围

接口：

```text
POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save
GET /api/my/route-plan-snapshots
GET /api/my/route-plan-snapshots/{snapshot_id}
```

交付：

```text
保存 candidate 创建 route_plan_snapshot
同一个 candidate_id 不能重复保存
列表只返回当前用户 snapshot
详情返回保存时刻 route_summary / planning_detail / evidence
支持 continue_trip_plan_id
当前不支持 user_note / share_text / saved_at / actions
当前列表不支持分页、status 或 keyword 查询
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-01_API_CONTRACT.md`
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
