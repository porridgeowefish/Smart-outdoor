# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
未登录不能上传 activity_track。
上传完成轨迹生成 activity_track。
上传完成轨迹不会创建 route_asset。
上传成功返回 parse_status=parsed。
上传成功返回 analysis.moving_time_seconds 和 analysis.analysis_json。
上传成功返回 ability_profile.generated_from_activity_track_ids。
上传成功返回 ability_profile.metrics_json。
不支持的文件类型返回 400 UNSUPPORTED_FILE_TYPE。
解析失败返回 400 TRACK_PARSE_FAILED。
GET /api/me/activity-tracks 返回当前用户活动列表。
GET /api/me/activity-tracks 返回 month、location、pace_or_speed、activity_date、analysis_json。
GET /api/me/ability-profile 返回当前用户画像。
没有画像时 GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。
```

## Parser / Service 测试

```text
解析距离。
解析累计爬升。
解析移动时间。
生成 track_geojson。
生成 activity analysis_json。
activity_count 正确递增。
generated_from_activity_track_ids 覆盖参与画像的活动。
metrics_json 写入 algorithm_version 和 VAM 等补充指标。
confidence 规则正确。
recent_max_distance_km 正确。
recent_max_elevation_gain_m 正确。
活动列表按 activity_date desc、created_at desc 排序。
缺少反查位置时 location 返回 "待识别"。
```
