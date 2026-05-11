# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## POST /api/me/activity-tracks/upload

用途：上传用户已完成活动轨迹，保存为 `activity_track`，并重新计算当前用户能力画像。

Request:

```text
multipart/form-data
file: required, GPX / KML / GeoJSON
activity_date: optional, YYYY-MM-DD
source_type: optional, default manual_upload
```

Response:

```json
{
  "activity_track_id": "act_123",
  "parse_status": "parsed",
  "analysis": {
    "distance_km": 18.0,
    "elevation_gain_m": 1200.0,
    "elevation_loss_m": 1180.0,
    "elevation_min_m": 2600.0,
    "elevation_max_m": 3900.0,
    "moving_time_seconds": 23400,
    "analysis_json": {
      "algorithm_version": "ability_v1",
      "point_count": 1200,
      "effort_km": 28.0,
      "climb_density_m_per_km": 66.67,
      "avg_vam_m_per_h": 184.6,
      "best_vam_5min_m_per_h": 620.0,
      "best_vam_20min_m_per_h": 520.0,
      "best_vam_60min_m_per_h": 410.0,
      "has_time_data": true,
      "has_elevation_data": true,
      "analysis_quality": "good",
      "location": {
        "display_name": "北京市 延庆区"
      }
    }
  },
  "ability_profile": {
    "level": "normal",
    "endurance_score": 0.62,
    "climb_score": 0.58,
    "recent_max_distance_km": 18.0,
    "recent_max_elevation_gain_m": 1200.0,
    "activity_count": 1,
    "confidence": "low",
    "generated_from_activity_track_ids": ["act_123"],
    "metrics_json": {
      "algorithm_version": "ability_v1",
      "recent_max_effort_km": 28.0,
      "endurance_capacity_effort_km": 28.0,
      "best_vam_5min_m_per_h": 620.0,
      "best_vam_20min_m_per_h": 520.0,
      "best_vam_60min_m_per_h": 410.0,
      "typical_vam_60min_m_per_h": 410.0,
      "avg_climb_speed_m_per_min": 3.1
    },
    "message": "当前能力画像基于 1 条完成活动轨迹生成，可信度为低。"
  }
}
```

错误：

```json
{
  "code": "UNSUPPORTED_FILE_TYPE",
  "message": "Only GPX, KML, and GeoJSON activity tracks are supported"
}
```

```json
{
  "code": "TRACK_PARSE_FAILED",
  "message": "Activity track could not be parsed"
}
```

实现说明：

```text
上传成功固定返回 parse_status=parsed。
解析失败不会保存 activity_track，也不会生成 failed 状态记录；当前实现直接返回 400 TRACK_PARSE_FAILED。
activity_track 是用户已完成活动，不会创建 route_asset，也不会进入线路库。
```

## GET /api/me/activity-tracks

用途：获取当前用户已上传的完成活动轨迹列表，用于个人中心活动记录展示。

Response:

```json
{
  "tracks": [
    {
      "id": "act_123",
      "month": "5",
      "distance_km": 18.0,
      "elevation_gain_m": 1200.0,
      "moving_time_seconds": 23400,
      "pace_or_speed": "21'40\" /km",
      "activity_date": "2026-05-08",
      "location": "北京市 延庆区",
      "type": "hike",
      "analysis_json": {
        "algorithm_version": "ability_v1",
        "effort_km": 28.0,
        "analysis_quality": "good"
      }
    }
  ]
}
```

实现说明：

```text
列表按 activity_date desc、created_at desc 排序。
month 当前返回 activity_date.month 的字符串，例如 "5"。
location 来自 analysis_json.location.display_name；没有反查结果时返回 "待识别"。
type 当前固定为 "hike"。
pace_or_speed 根据 moving_time_seconds 和 distance_km 计算；缺少时间或距离无效时返回 "--"。
```

## GET /api/me/ability-profile

用途：获取当前用户能力画像。

Response:

```json
{
  "level": "normal",
  "endurance_score": 0.62,
  "climb_score": 0.58,
  "recent_max_distance_km": 18.0,
  "recent_max_elevation_gain_m": 1200.0,
  "activity_count": 1,
  "confidence": "low",
  "generated_from_activity_track_ids": ["act_123"],
  "metrics_json": {
    "algorithm_version": "ability_v1",
    "recent_max_effort_km": 28.0,
    "endurance_capacity_effort_km": 28.0,
    "best_vam_5min_m_per_h": 620.0,
    "best_vam_20min_m_per_h": 520.0,
    "best_vam_60min_m_per_h": 410.0,
    "typical_vam_60min_m_per_h": 410.0,
    "avg_climb_speed_m_per_min": 3.1
  },
  "message": "当前能力画像基于 1 条完成活动轨迹生成，可信度为低。"
}
```

错误：

```json
{
  "code": "ABILITY_PROFILE_NOT_FOUND",
  "message": "Ability profile not found"
}
```

实现说明：

```text
当前实现不会在 0 条活动时返回 unknown profile。
如果用户尚未上传成功过 activity_track，GET /api/me/ability-profile 返回 404 ABILITY_PROFILE_NOT_FOUND。
```
