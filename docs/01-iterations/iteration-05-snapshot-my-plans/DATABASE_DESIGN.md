# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

## route_plan_snapshots

用户保存到“我的规划”的一份线路规划快照。

关键字段：

```text
id
user_id
continue_trip_plan_id
source_candidate_id
route_asset_id
route_summary
recommendation_reason
advantage_tags
score_breakdown
planning_detail
evidence
created_at
```

## 约束

```text
UNIQUE(source_candidate_id)
```

## 规则

```text
点击候选详情不创建 snapshot
点击保存才创建 snapshot
snapshot 保存当时内容，不随 route_asset 后续变化自动变化
列表只返回 current_user 的 snapshot
详情可以跳回原 trip_plan 继续对话
当前不保存 user_note / share_text / saved_at
```
