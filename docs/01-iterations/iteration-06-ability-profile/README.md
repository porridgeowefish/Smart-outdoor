# Iteration 06 Ability Profile

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation plus this iteration directory.

## 用户闭环

用户可以上传自己已完成的活动轨迹，系统保存为完成活动记录，并生成基础能力画像。个人中心可以查看活动记录和当前能力画像。

## 本轮目标

```text
上传完成轨迹生成 activity_track。
解析距离、爬升、移动时间和能力分析指标。
提供当前用户 activity_track 列表。
生成 user_ability_profile。
上传 activity_track 不创建 route_asset，不污染线路库。
```

## 范围

### 本轮覆盖

```text
POST /api/me/activity-tracks/upload 上传完成轨迹并刷新能力画像。
GET /api/me/activity-tracks 查看当前用户完成活动列表。
GET /api/me/ability-profile 查看当前用户能力画像。
```

### 暂不进入

```text
不做 activity_track → route_asset 的转化或线路库回流。
不做画像多版本或历史快照。
不做更多运动类型（type 当前固定 hike）。
不做管理员维护后台。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md
- docs/99-archive/backend-docs-legacy/US-02_PROFILE_AND_ABILITY_DESIGN.md
- docs/99-archive/backend-docs-legacy/US-01_DATABASE_DESIGN.md
