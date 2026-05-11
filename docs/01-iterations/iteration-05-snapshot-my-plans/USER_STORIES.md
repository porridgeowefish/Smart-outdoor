# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-05.1 保存候选到我的规划

作为用户，我希望把有价值的候选线路保存到“我的规划”，以便之后反复查看。

验收要点：

```text
保存 candidate 创建 route_plan_snapshot
同一个 candidate_id 最多保存一次
保存的是当时的规划内容快照
当前保存接口不接收 note
```

## US-05.2 查看我的规划列表

作为用户，我希望查看已保存的规划卡片，以便继续比较和决策。

验收要点：

```text
只返回当前用户的 snapshot
列表展示 route 摘要、优势标签、推荐理由和 created_at
当前列表无分页、status 或 keyword 查询
```

## US-05.3 查看规划快照详情

作为用户，我希望查看保存时刻的规划详情，以便回看当时的理由、风险和证据。

验收要点：

```text
返回保存时刻 route_summary
返回保存时刻 planning_detail
返回保存时刻 evidence
支持 continue_trip_plan_id
支持通过 route.route_id 进入线路资产详情
当前不返回 user_note / share_text / actions
不自动刷新天气、交通、路况
```
