# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: ORM model and migrations when introduced.

## activity_tracks

用户已完成活动记录，用于能力画像。它和 `route_asset` 是两个不同业务对象，不能混用。

关键字段：

```text
id
user_id
file_url
file_type
file_size_bytes
checksum
source_type
activity_date
distance_km
elevation_gain_m
elevation_loss_m
elevation_min_m
elevation_max_m
duration_seconds
moving_time_seconds
track_geojson
analysis_json
created_at
updated_at
```

`analysis_json` 当前保存能力画像所需的派生指标：

```text
algorithm_version
point_count
effort_km
climb_density_m_per_km
avg_vam_m_per_h
best_vam_5min_m_per_h
best_vam_20min_m_per_h
best_vam_60min_m_per_h
has_time_data
has_elevation_data
analysis_quality
location
```

## user_ability_profiles

用户当前能力画像。每个用户最多一条画像记录，上传新的 `activity_track` 后重新计算。

关键字段：

```text
id
user_id
level
endurance_score
climb_score
recent_max_distance_km
recent_max_elevation_gain_m
activity_count
confidence
generated_from_activity_track_ids
metrics_json
message
created_at
updated_at
```

`metrics_json` 当前保存画像计算过程中的补充指标：

```text
algorithm_version
recent_max_effort_km
endurance_capacity_effort_km
best_vam_5min_m_per_h
best_vam_20min_m_per_h
best_vam_60min_m_per_h
typical_vam_60min_m_per_h
avg_climb_speed_m_per_min
```

## Confidence 规则

当前实现不只按活动数量判断，还会参考活动分析质量：

```text
activity_count = 0 -> unknown
activity_count <= 2 且 good quality 活动少于 2 条 -> low
activity_count <= 2 且 good quality 活动至少 2 条 -> medium
activity_count 3-4 -> medium
activity_count >= 5 -> high
```

## 边界

```text
activity_track 是完成记录，route_asset 是线路资产。
activity_track 默认不进入线路库。
route_asset 不会自动成为 activity_track。
上传 activity_track 成功会更新 user_ability_profile。
上传 activity_track 失败不会保存 failed 状态记录。
```
