# Iteration 05 Snapshot / 我的规划

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this iteration directory; implementation (ORM model, Pydantic schemas, router, tests) is authoritative after this slice landed.

## 用户闭环

用户在候选线路里看中一条，可以把它保存到“我的规划”；之后随时从“我的规划”查看保存时刻的规划卡片和详情，并能回到来源 TripPlan 继续对话。

## 本轮目标

```text
用户可以把候选线路保存为“我的规划”快照。
用户可以查看自己已保存的规划快照列表和详情。
快照保存的是当时的规划内容，不随后续线路资产变化自动更新。
```

## 范围

### 本轮覆盖

```text
保存 candidate 创建 route_plan_snapshot。
同一个 candidate 不能重复保存。
列表只返回当前用户的 snapshot。
详情返回保存时刻 route_summary / planning_detail / evidence。
详情支持 continue_trip_plan_id 回到来源 TripPlan。
```

### 暂不进入

```text
不做列表分页、status / keyword 查询。
不保存 user_note / share_text / actions。
不自动刷新天气、交通、路况等证据。
```

## 历史来源

- [MVP_IMPLEMENTATION_SLICES.md](../../99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md)
- [US-01_API_CONTRACT.md](../../99-archive/backend-docs-legacy/US-01_API_CONTRACT.md)
- [US-01_DATABASE_DESIGN.md](../../99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md)
