# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-06.1 上传已完成活动轨迹

作为用户，我希望上传自己已经完成过的轨迹，以便系统了解我的真实户外能力。

验收要点：

```text
上传 activity_track。
不会创建 route_asset。
保存原始轨迹文件。
解析距离、爬升、移动时间和轨迹分析指标。
解析失败返回 400 TRACK_PARSE_FAILED，不保存 activity_track。
不支持的文件类型返回 400 UNSUPPORTED_FILE_TYPE。
```

## US-06.2 生成能力画像

作为用户，我希望系统根据完成轨迹生成能力画像，以便推荐更符合我的能力。

验收要点：

```text
生成 endurance_score。
生成 climb_score。
生成 level。
activity_count 正确递增。
generated_from_activity_track_ids 记录画像来源活动。
metrics_json 返回画像计算补充指标。
confidence 按活动数量和分析质量变化。
```

## US-06.3 查看活动记录列表

作为用户，我希望在个人中心查看已经上传的完成活动，确认这些活动是否被纳入能力画像。

验收要点：

```text
GET /api/me/activity-tracks 返回当前用户活动列表。
返回 month、distance_km、elevation_gain_m、moving_time_seconds。
返回 pace_or_speed、activity_date、location、type。
返回 analysis_json，便于前端展示分析摘要。
活动列表不会混入 route_asset。
```

## US-06.4 查看能力画像

作为用户，我希望在个人中心查看我的能力画像和可信度提示。

验收要点：

```text
返回 level、endurance_score、climb_score、recent_max_distance_km、recent_max_elevation_gain_m、activity_count、confidence。
返回 generated_from_activity_track_ids、metrics_json、message。
没有成功上传过 activity_track 时，GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。
```
