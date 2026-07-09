# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM model (`RoutePlanSnapshot`) and migrations.

## 表

```text
新增 route_plan_snapshots。
复用 trip_plans、trip_plan_candidate_routes（作为外键来源）。
```

## route_plan_snapshots

用户保存到“我的规划”的一份线路规划快照。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | uuid 字符串（36） | primary key，默认 uuid4 | 新增 |
| user_id | str | 用户 ID（36） | 索引；来自当前登录用户 | 新增 |
| continue_trip_plan_id | str | TripPlan ID（36） | foreign key: trip_plans.id；索引 | 新增 |
| source_candidate_id | str | 候选 ID（36） | foreign key: trip_plan_candidate_routes.id；索引；unique | 新增 |
| route_asset_id | str | 线路资产 ID（36） | 索引；保存时从候选复制 | 新增 |
| route_summary | object | 见 ORM model（CandidateRouteSummary 结构：route_id / name / location / distance_km / elevation_gain_m / cover_image_url / display_tags / track_preview） | JSON；保存时复制候选 route 摘要 | 新增 |
| recommendation_reason | str | 推荐理由文本 | Text；保存时从候选复制 | 新增 |
| advantage_tags | array[str] | 优势标签列表 | JSON；保存时从候选复制 | 新增 |
| score_breakdown | object | 见 ORM model | JSON；保存时从候选复制 | 新增 |
| planning_detail | object | 见 ORM model（候选 planning_detail 结构） | JSON；保存时复制 | 新增 |
| evidence | object | 见 ORM model（候选 evidence 结构） | JSON；保存时复制 | 新增 |
| created_at | datetime | tz-aware 时间戳 | server generated（_utc_now） | 新增 |

## 约束

```text
UNIQUE(source_candidate_id)：同一候选最多保存一次（约束名 uq_route_plan_snapshot_candidate）。
列表查询只返回 current_user 的 snapshot。
snapshot 保存当时内容，不随 route_asset 后续变化自动变化。
当前不保存 user_note / share_text / saved_at。
```

## 迁移与同步点

```text
新增 route_plan_snapshots 表及其 UniqueConstraint。
保存接口须复制候选的 route_summary / planning_detail / evidence / advantage_tags / score_breakdown / recommendation_reason。
列表与详情读取须按 user_id 过滤。
```
