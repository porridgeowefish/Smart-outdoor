# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
保存 candidate 创建 route_plan_snapshot
重复保存同一 candidate 返回 ROUTE_PLAN_SNAPSHOT_EXISTS
我的规划列表只返回当前用户 snapshot
列表返回 total 和 items
详情返回 route_summary
详情返回 planning_detail
详情返回 evidence
详情返回 continue_trip_plan_id
其他用户不能访问 snapshot
```

## Service 测试

```text
保存时复制候选详情内容
保存后 route_asset 变化不影响 snapshot 内容
当前不保存 user_note
```
