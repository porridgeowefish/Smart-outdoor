# API Contract

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|
| POST | `/api/me/activity-tracks/upload` | 新增 |
| GET | `/api/me/activity-tracks` | 新增 |
| GET | `/api/me/ability-profile` | 新增 |

三个端点均要求登录（401 UNAUTHORIZED 未登录访问）。

## POST /api/me/activity-tracks/upload

用途：上传用户已完成活动轨迹，保存为完成活动记录，并重新计算当前用户能力画像。

Request（multipart/form-data）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | binary | 是 | GPX / KML / GeoJSON 轨迹文件 |
| activity_date | str (YYYY-MM-DD) | 否 | 活动日期，缺省时从轨迹时间或当天推导 |
| source_type | str | 否 | 来源类型，默认 `manual_upload` |

Response：

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

## GET /api/me/activity-tracks

用途：获取当前用户已上传的完成活动轨迹列表，用于个人中心活动记录展示。

Response：

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

## GET /api/me/ability-profile

用途：获取当前用户能力画像。

Response：

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

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 401 | UNAUTHORIZED | 未登录或登录已失效（三个端点通用）。 |
| 400 | UNSUPPORTED_FILE_TYPE | upload 收到非 GPX / KML / GeoJSON 文件类型。 |
| 400 | TRACK_PARSE_FAILED | upload 轨迹无法解析。 |
| 404 | ABILITY_PROFILE_NOT_FOUND | 当前用户尚无能力画像（未上传成功任何完成轨迹）。 |

## 历史来源

- DATABASE_DESIGN.md（`activity_tracks` / `user_ability_profiles` 表与 JSON 子键）
- DELIVERY_NOTES.md（解析失败不落 failed 记录、`parse_status` 固定为 parsed 等实现说明）
