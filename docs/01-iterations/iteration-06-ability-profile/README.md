# Iteration 06 Ability Profile

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以上传自己已完成的活动轨迹，系统保存为 `activity_track`，并生成基础能力画像。个人中心可以查看活动记录和当前能力画像。

## 范围

接口：

```text
POST /api/me/activity-tracks/upload
GET /api/me/activity-tracks
GET /api/me/ability-profile
```

核心对象：

```text
activity_tracks
user_ability_profiles
```

交付：

```text
上传完成轨迹生成 activity_track。
上传 activity_track 不会创建 route_asset。
解析距离、爬升、移动时间和能力分析指标。
提供当前用户 activity_track 列表。
生成 user_ability_profile。
返回 generated_from_activity_track_ids 和 metrics_json。
activity_count 正确递增。
confidence 按活动数量和分析质量变化。
没有画像时 GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。
```

## 历史来源

- `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`
- `docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md`
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
