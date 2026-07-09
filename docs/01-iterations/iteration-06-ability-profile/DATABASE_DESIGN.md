# Database Design

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM models and migrations.

## 表

```text
新增 activity_tracks。
新增 user_ability_profiles。
复用 users。
```

`activity_tracks` 与 `route_assets` 是两个不同业务对象，不能混用；边界论证与上传失败不落 failed 记录等设计说明见 DELIVERY_NOTES。

## activity_tracks

用户已完成活动记录，用于能力画像。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key | 新增 |
| user_id | str | UUID 字符串 | foreign key: users.id, indexed | 新增 |
| file_url | str | 静态资源路径 | server generated | 新增 |
| file_type | str | `gpx` / `kml` / `geojson` | parse from filename | 新增 |
| file_size_bytes | int\|null | 字节数 | nullable | 新增 |
| checksum | str\|null | sha256 hex | nullable | 新增 |
| source_type | str | 默认 `manual_upload` | default | 新增 |
| activity_date | date\|null | YYYY-MM-DD | nullable; 缺省从轨迹推导 | 新增 |
| distance_km | float | 公里 | required | 新增 |
| elevation_gain_m | float | 米 | required | 新增 |
| elevation_loss_m | float\|null | 米 | nullable | 新增 |
| elevation_min_m | float\|null | 米 | nullable | 新增 |
| elevation_max_m | float\|null | 米 | nullable | 新增 |
| duration_seconds | int\|null | 秒 | nullable | 新增 |
| moving_time_seconds | int\|null | 秒 | nullable | 新增 |
| track_geojson | object | GeoJSON Feature | required | 新增 |
| analysis_json | object | 见 analysis_json schema | default `{}` | 新增 |
| created_at | datetime | UTC | server generated | 新增 |
| updated_at | datetime | UTC | server generated | 新增 |

### analysis_json 子键（JSON schema）

```text
{
  algorithm_version: str,
  point_count: int|null,
  effort_km: float|null,
  climb_density_m_per_km: float|null,
  avg_vam_m_per_h: float|null,
  best_vam_5min_m_per_h: float|null,
  best_vam_20min_m_per_h: float|null,
  best_vam_60min_m_per_h: float|null,
  has_time_data: bool,
  has_elevation_data: bool,
  analysis_quality: "good" | "medium" | "low",
  location: { display_name: str }   # Optional；反查失败时缺省
}
```

## user_ability_profiles

用户当前能力画像。每个用户最多一条记录（`user_id` 唯一），上传新的完成轨迹后重新计算。

| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| id | str | UUID 字符串 | primary key | 新增 |
| user_id | str | UUID 字符串 | foreign key: users.id, unique, indexed | 新增 |
| level | str | `beginner` / `normal` / `strong` / `unknown` | default `unknown` | 新增 |
| endurance_score | float\|null | 0.0–1.0 归一化 | nullable | 新增 |
| climb_score | float\|null | 0.0–1.0 归一化 | nullable | 新增 |
| recent_max_distance_km | float\|null | 公里 | nullable | 新增 |
| recent_max_elevation_gain_m | float\|null | 米 | nullable | 新增 |
| activity_count | int | 完成轨迹数 | default 0 | 新增 |
| confidence | str | `unknown` / `low` / `medium` / `high` | default `unknown` | 新增 |
| generated_from_activity_track_ids | array[str] | UUID 字符串 | default `[]` | 新增 |
| metrics_json | object | 见 metrics_json schema | default `{}` | 新增 |
| message | str\|null | 中文画像说明 | nullable | 新增 |
| created_at | datetime | UTC | server generated | 新增 |
| updated_at | datetime | UTC | server generated | 新增 |

### metrics_json 子键（JSON schema）

```text
{
  algorithm_version: str,
  recent_max_effort_km: float|null,
  endurance_capacity_effort_km: float|null,
  best_vam_5min_m_per_h: float|null,
  best_vam_20min_m_per_h: float|null,
  best_vam_60min_m_per_h: float|null,
  typical_vam_60min_m_per_h: float|null,
  avg_climb_speed_m_per_min: float|null
}
```

## 约束

```text
user_ability_profiles.user_id 唯一，每个用户最多一条画像。
activity_tracks.user_id 非唯一，一个用户可有多条完成轨迹。
上传成功 activity_track 后触发该用户 user_ability_profile 的重新计算。
```

## 迁移与同步点

```text
新增 activity_tracks 表。
新增 user_ability_profiles 表。
上传端点写入 activity_tracks 并刷新对应 user_ability_profiles。
activity 列表与 ability-profile 端点分别读取这两张表。
轨迹文件落本地静态目录（config activity_storage_dir），不入线路库。
```

## 历史来源

- DELIVERY_NOTES.md（activity_track vs route_asset 边界、confidence 规则、parse_status 固定值等设计说明）
- backend/app/features/users/model.py（ORM 类型）
