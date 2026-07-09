# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests.

## Service / Unit

- [US-06.1] 解析距离 / 累计爬升 / 移动时间 / 生成 track_geojson → 生成 activity analysis_json。
- [US-06.1] 不支持的文件类型 → `UnsupportedRouteFileTypeError`。
- [US-06.1] 轨迹无法解析 → `ActivityTrackParseError`，不写 activity_track。
- [US-06.2] activity_count 按完成轨迹数正确递增。
- [US-06.2] generated_from_activity_track_ids 覆盖参与画像的活动。
- [US-06.2] metrics_json 写入 algorithm_version 与 VAM / 爬升速度等补充指标。
- [US-06.2] confidence 规则正确（活动数量 + good quality 数量）。
- [US-06.2] recent_max_distance_km / recent_max_elevation_gain_m 取参与活动的最大值。
- [US-06.3] 活动列表按 activity_date desc、created_at desc 排序。
- [US-06.3] pace_or_speed 由 moving_time_seconds 与 distance_km 计算；缺时间或距离无效 → `"--"`。
- [US-06.3] location 取 analysis_json.location.display_name；反查失败 → `"待识别"`。
- [US-06.3] month 为 activity_date.month 的字符串。
- [US-06.3] type 当前固定为 `"hike"`。

## API

- [US-06.1] 上传完成轨迹 → 创建 activity_track，不创建 route_asset。
- [US-06.1] 上传成功返回 parse_status=parsed、analysis.moving_time_seconds、analysis.analysis_json。
- [US-06.1] 上传成功返回 ability_profile.generated_from_activity_track_ids 与 metrics_json。
- [US-06.3] GET /api/me/activity-tracks 返回当前用户活动列表（含 month / location / pace_or_speed / activity_date / analysis_json）。
- [US-06.3] 上传后反查位置结果存入 analysis_json.location.display_name，列表 location 读取该字段。
- [US-06.4] GET /api/me/ability-profile 返回当前用户画像。
- [US-06.2] 多次上传后 activity_count 与 confidence 随活动数累积。

## 权限

- 三个端点未登录访问 → 401 UNAUTHORIZED。

## 失败路径

- [US-06.1] upload 非 GPX / KML / GeoJSON 文件类型 → 400 UNSUPPORTED_FILE_TYPE。
- [US-06.1] upload 轨迹无法解析 → 400 TRACK_PARSE_FAILED。
- [US-06.4] 当前用户尚无能力画像 → GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。

## 验证命令

```powershell
pytest backend/tests/users/test_activity_ability_api.py
```
