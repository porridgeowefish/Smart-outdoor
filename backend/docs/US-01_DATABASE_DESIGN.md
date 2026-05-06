# US-01 数据库设计：对话规划去哪

## 1. 设计原则

US-01 数据库设计从接口反推，核心问题是：系统必须长期记住什么，哪些对象需要通过 ID 再次访问，哪些内容需要稳定保存。

MVP 采用简单鲁棒设计：

1. `trip_plans` 保存一次规划任务的当前状态和压缩记忆。
2. `trip_plan_messages` 保存真实发生过的用户与 Agent 交互。
3. `agent_runs` 保存每次用户消息触发的 Agent 后台运行。
4. `route_assets` 保存线路资产主档。
5. `route_files` 保存 KML / GPX / GeoJSON 原始轨迹文件。
6. `route_analysis_snapshots` 保存轨迹解析后的线路技术指标。
7. `trip_plan_candidate_routes` 保存 Agent 在某次规划中推荐过的候选线路。
8. `route_plan_snapshots` 保存用户明确保存到“我的规划”的规划快照。

MVP 中涉及动态上下文、轨迹分析扩展指标、规划详情和证据的字段统一使用 `JSON`，而不是过早引入 JSONB 或 PostGIS。当前用户故事不要求按 JSON 内部字段查询，也不要求复杂空间查询。

## 2. trip_plans

### 含义

`trip_plans` 表示一次由用户对话触发的规划任务。它不是线路，不是候选，不是快照，也不是一次 Agent 运行。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 规划对话 ID。 |
| user_id | string/uuid | 所属用户。 |
| title | string | Agent 生成的标题，例如“成都周边一日雪山徒步”。 |
| status | enum/string | `draft / active / closed`。 |
| context_summary | text | 当前规划上下文的自然语言压缩摘要。 |
| context_state | JSON | Agent 对当前规划的结构化理解。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |
| closed_at | datetime/null | 关闭时间。 |

### status 定义

| 状态 | 含义 |
|---|---|
| draft | 第一条消息后创建，Agent 尚未达到推荐条件，主要用于接住用户和继续追问。 |
| active | 达到信息充分度阈值，或已经产生过候选线路，可以推荐、比较、保存快照、继续对话。 |
| closed | 用户手动结束，或长期无操作后系统归档；只读，不允许继续追加消息。 |

### context_state 示例

```json
{
  "activity_goal": "看雪山",
  "departure_area": "成都",
  "time_window": {
    "raw_text": "周末",
    "start_date": "2026-05-09",
    "end_date": "2026-05-10",
    "duration_days": 1
  },
  "transport_hint": "self_drive",
  "ability_hint": {
    "level": "normal",
    "max_distance_km": null,
    "max_elevation_gain_m": null
  },
  "preference_hint": {
    "scenery": ["雪山"],
    "risk_tolerance": "medium"
  }
}
```

### 设计取舍

`context_state` 使用 JSON。MVP 只把它作为 Agent 的结构化上下文存档和恢复对象；后端整体读取、整体合并、整体保存；数据库不负责理解内部字段。Pydantic 负责结构校验。后续如果出现内部字段查询、统计或索引需求，再迁移 JSONB。

## 3. trip_plan_messages

### 含义

`trip_plan_messages` 保存一次 `trip_plan` 下真实发生过的用户消息和 Agent 消息。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 消息 ID。 |
| trip_plan_id | string/uuid | 所属规划对话。 |
| agent_run_id | string/uuid/null | 关联 AgentRun。 |
| role | enum/string | `user / assistant`。 |
| content | text | 消息正文。 |
| content_type | enum/string | MVP 默认 `text`。 |
| created_at | datetime | 消息创建时间。 |

### 规则

1. `role` 只保留 `user / assistant`。
2. system prompt 不进入消息表。
3. tool 调用日志不进入消息表。
4. 候选线路卡片不进入消息表，进入 `trip_plan_candidate_routes`。
5. Agent 流式输出完成后，后端写入一条 assistant 消息。

### 与 LLM 上下文的关系

LLM 调用时通常组合：

```text
trip_plans.context_summary
+ trip_plans.context_state
+ 最近 N 条 trip_plan_messages
+ 当前用户消息
```

## 4. agent_runs

### 含义

`agent_runs` 表示一次 Agent 后台运行。用户每发送一条消息，就创建一个新的 AgentRun。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | AgentRun ID。 |
| trip_plan_id | string/uuid | 所属规划对话。 |
| trigger_message_id | string/uuid | 触发本次运行的用户消息。 |
| run_status | enum/string | 执行状态。 |
| phase | enum/string | 当前工作阶段。 |
| error_code | string/null | 失败错误码。 |
| error_message | text/null | 失败原因。 |
| started_at | datetime/null | 实际开始时间。 |
| completed_at | datetime/null | 完成时间。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### run_status

| 状态 | 含义 |
|---|---|
| queued | 任务已创建，等待执行。 |
| running | Agent 正在执行。 |
| waiting_user | Agent 已完成当前轮判断，但需要用户补充信息。 |
| succeeded | 成功完成，生成回复或候选结果。 |
| partial | 部分成功，例如生成了回复，但外部搜索失败。 |
| failed | 不可用失败。 |
| cancelled | 被系统或用户取消。 |

### phase

| 阶段 | 含义 |
|---|---|
| intent_detection | 意图识别。 |
| context_update | 上下文抽取和更新。 |
| sufficiency_check | 信息充分度判断。 |
| route_retrieval | 线路召回。 |
| evidence_search | 外部证据搜索。 |
| plan_evaluation | 方案评估。 |
| response_generation | 回复生成。 |
| snapshot_generation | 快照内容生成。 |

`phase` 不是状态机，只是 Agent 当前正在做什么，用于 SSE、后台调试和失败定位。

## 5. route_assets

### 含义

`route_assets` 是系统线路库中的一条线路资产。它是核心资产，不是某次规划结果。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 线路资产 ID。 |
| name | string | 线路名称。 |
| description | text/null | 线路简介。 |
| cover_image_url | string/null | 卡片封面图。 |
| manual_tags | JSON | 用户导入轨迹时补充的多选标签。 |
| source_type | enum/string | `system / user_upload / admin_import / external`。 |
| source_name | string/null | 来源名称。 |
| visibility | enum/string | `public / private`。 |
| status | enum/string | `active / pending_review / disabled`。 |
| created_by_user_id | string/uuid/null | 创建用户。系统或管理员导入可为空。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### 规则

1. `route_assets` 是线路本体。
2. 它不等于用户保存的规划。
3. 它不等于一次 Agent 推荐候选。
4. 它可以被多个 `trip_plan_candidate_routes` 引用。
5. 它可以被多个 `route_plan_snapshots` 引用。
6. 距离、爬升、海拔等技术指标不放在这里，放在 `route_analysis_snapshots`。

## 6. route_files

### 含义

`route_files` 保存线路资产关联的原始轨迹文件，例如 KML、GPX、GeoJSON。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 轨迹文件 ID。 |
| route_asset_id | string/uuid | 所属线路资产。 |
| file_url | string | 文件存储地址。 |
| file_type | enum/string | `kml / gpx / geojson`。 |
| file_size_bytes | integer/null | 文件大小。 |
| checksum | string/null | 文件哈希，用于去重和校验。 |
| uploaded_by_user_id | string/uuid/null | 上传者。系统导入可为空。 |
| parse_status | enum/string | `pending / parsed / failed`。 |
| parse_error | text/null | 解析失败原因。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### 规则

1. 一个 `route_asset` 可以关联多个 `route_file`。
2. MVP 业务只使用一个主轨迹文件。
3. 文件解析成功后，生成 `route_analysis_snapshots`。
4. `route_files` 只管原始文件，不保存分析指标。

## 7. route_analysis_snapshots

### 含义

`route_analysis_snapshots` 保存某个轨迹文件解析后得到的一份线路分析结果。它是线路本身的客观技术指标，不是用户规划结果。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 分析快照 ID。 |
| route_asset_id | string/uuid | 所属线路资产。 |
| route_file_id | string/uuid | 来源轨迹文件。 |
| distance_km | decimal | 总距离。 |
| elevation_gain_m | decimal | 累计爬升。 |
| elevation_loss_m | decimal/null | 累计下降。 |
| elevation_min_m | decimal/null | 最低海拔。 |
| elevation_max_m | decimal/null | 最高海拔。 |
| climb_ratio | decimal/null | 爬升比，例如 `elevation_gain_m / distance_km`。 |
| steep_ratio | decimal/null | 陡坡比。 |
| start_point | JSON | 起点坐标。 |
| end_point | JSON | 终点坐标。 |
| bounds | JSON | 轨迹边界。 |
| center_point | JSON | 中心点。 |
| track_geojson | JSON | 简化后的 GeoJSON 轨迹，用于前端地图渲染。 |
| analysis_json | JSON | 更多分析指标。 |
| created_at | datetime | 创建时间。 |

### analysis_json 示例

```json
{
  "slope_distribution": {
    "flat": 0.25,
    "moderate": 0.5,
    "steep": 0.25
  },
  "altitude_bands": [
    {"min_m": 0, "max_m": 1000, "ratio": 0.1},
    {"min_m": 1000, "max_m": 3000, "ratio": 0.6},
    {"min_m": 3000, "max_m": 5000, "ratio": 0.3}
  ],
  "technical_notes": ["存在连续爬升段", "最高海拔超过 4000m"]
}
```

### 设计取舍

空间字段和 	rack_geojson MVP 使用 JSON，不引入 PostGIS geometry。当前用户故事不要求复杂空间查询；JSON 足够支持前端展示、Agent 推荐和线路详情。后续如果需要附近线路搜索、空间范围检索或地图框选，再引入 PostGIS。

## 8. trip_plan_candidate_routes

### 含义

`trip_plan_candidate_routes` 表示一次 `trip_plan` 里，Agent 推荐过的一条候选线路。它是 `trip_plan` 和 `route_asset` 之间的推荐关系。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 候选 ID，也就是接口里的 `candidate_id`。 |
| trip_plan_id | string/uuid | 所属规划对话。 |
| agent_run_id | string/uuid | 由哪次 AgentRun 推荐。 |
| route_asset_id | string/uuid | 候选线路本体。 |
| route_analysis_snapshot_id | string/uuid | 推荐时使用的线路分析快照。 |
| rank | integer | 推荐排序，通常 1 / 2 / 3。 |
| advantage_tags | JSON | 优势标签。 |
| recommendation_reason | text/null | 推荐理由摘要。 |
| score_breakdown | JSON/null | 推荐评分拆解。 |
| created_at | datetime | 创建时间。 |

### score_breakdown 示例

```json
{
  "ability_match": 0.82,
  "scenery_match": 0.9,
  "transport_fit": 0.76,
  "risk_penalty": 0.2,
  "overall": 0.84
}
```

### 规则

1. 每次 Agent 推荐默认生成 3 条候选。
2. 候选卡片展示字段来自 `route_asset + route_analysis_snapshot + advantage_tags`。
3. 点击候选卡片时，通过 `candidate_id` 查详情。
4. 候选可被保存为 `route_plan_snapshot`。
5. 同一 `trip_plan` 可以有多轮候选推荐。
6. 同一 `trip_plan` 下，同一 `route_asset_id` 允许重复出现在候选里，因为用户需求和推荐理由可能变化。

## 9. route_plan_snapshots

### 含义

`route_plan_snapshots` 表示用户保存到“我的规划”的一份线路规划快照。

用户保存的不是单纯 `route_id`，而是这条线路在本次对话语境下的规划结果。

### 字段

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 快照 ID。 |
| user_id | string/uuid | 所属用户。 |
| trip_plan_id | string/uuid | 来源规划对话。 |
| candidate_route_id | string/uuid | 来源候选线路。一个 candidate 只能保存一次。 |
| route_asset_id | string/uuid | 线路本体。 |
| route_analysis_snapshot_id | string/uuid | 保存时使用的线路分析快照。 |
| title | string | 快照标题，通常为线路名称。 |
| cover_image_url | string/null | 卡片封面图。 |
| route_summary | JSON | 保存卡片和线路基础指标。 |
| planning_detail | JSON | 保存本次规划语境下的详细建议。 |
| evidence | JSON | 保存当时参考的证据来源。 |
| share_text | text/null | 可复制分享文本。 |
| user_note | text/null | 用户备注。 |
| saved_at | datetime | 用户点击保存的时间。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### route_summary 示例

```json
{
  "name": "四姑娘山大峰",
  "distance_km": 15.2,
  "elevation_gain_m": 1320,
  "elevation_min_m": 3200,
  "elevation_max_m": 5025,
  "advantage_tags": ["雪山体验", "交通便利"],
  "start_point": {"name":"海子沟入口","lon":102.9,"lat":31.0},
  "end_point": {"name":"海子沟入口","lon":102.9,"lat":31.0}
}
```

### planning_detail 示例

```json
{
  "fit_reason": "适合你这次从成都出发、一日往返、想看雪山并接受一定挑战的需求。",
  "risk_notes": ["海拔较高，存在高反风险。", "爬升较大，不适合完全新手。"],
  "transport_plan": {"summary":"建议自驾前往，成都出发约 4-5 小时到达。","estimated_duration_minutes":270,"transport_mode":"self_drive"},
  "weather_summary": {"summary":"保存时天气判断，仅供参考，出发前应刷新。","forecast_date":"2026-05-09","weather_text":"多云","temp_min_c":2,"temp_max_c":12},
  "budget_estimate": {"currency":"CNY","min_amount":300,"max_amount":600},
  "gear_suggestions": ["防风保暖层", "头灯", "登山杖"]
}
```

### 规则

1. 点击候选详情不创建 snapshot。
2. 点击“保存到我的规划”才创建 snapshot。
3. 一个 `trip_plan` 可以有多个 snapshot。
4. 一个 `candidate_route_id` 只能保存一次。
5. snapshot 保存当时内容，不随 `route_asset` 后续变化自动变化。
6. 我的规划列表展示 snapshot 卡片。
7. snapshot 详情可以跳回原 `trip_plan` 继续对话。

### 唯一约束

```sql
UNIQUE(candidate_route_id)
```

用于保证同一个候选线路不能重复保存。

## 10. 最小关系总结

```text
trip_plans 1:N trip_plan_messages
trip_plans 1:N agent_runs
trip_plans 1:N trip_plan_candidate_routes
trip_plans 1:N route_plan_snapshots
route_assets 1:N route_files
route_assets 1:N route_analysis_snapshots
route_assets 1:N trip_plan_candidate_routes
route_assets 1:N route_plan_snapshots
route_files 1:N route_analysis_snapshots
agent_runs 1:N trip_plan_candidate_routes
trip_plan_candidate_routes 1:0..1 route_plan_snapshots
```


## 11. US-02 用户与能力画像补充

US-02 为总数据模型补充三张表：

```text
users
activity_tracks
user_ability_profiles
```

### users

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 用户 ID。 |
| username | string/null | 登录名，可空，唯一。 |
| phone | string/null | 手机号，可空，唯一。 |
| email | string/null | 邮箱，可空，唯一。 |
| password_hash | string | 密码哈希，不能存明文。 |
| nickname | string | 展示昵称。 |
| avatar_url | string/null | 头像地址。 |
| role | enum/string | `user / admin`。 |
| status | enum/string | `active / disabled`。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |
| last_login_at | datetime/null | 最后登录时间。 |

### activity_tracks

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 活动轨迹 ID。 |
| user_id | string/uuid | 所属用户。 |
| file_url | string | 原始轨迹文件地址。 |
| file_type | enum/string | `kml / gpx / geojson`。 |
| file_size_bytes | integer/null | 文件大小。 |
| checksum | string/null | 文件哈希。 |
| source_type | enum/string | `manual_upload / watch_import / app_import`。MVP 只实现 `manual_upload`。 |
| activity_date | date/null | 活动发生日期。 |
| distance_km | decimal | 距离。 |
| elevation_gain_m | decimal | 累计爬升。 |
| elevation_loss_m | decimal/null | 累计下降。 |
| elevation_min_m | decimal/null | 最低海拔。 |
| elevation_max_m | decimal/null | 最高海拔。 |
| duration_seconds | integer/null | 总用时。 |
| moving_time_seconds | integer/null | 移动用时。 |
| track_geojson | JSON | 简化轨迹。 |
| analysis_json | JSON | 扩展分析指标。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

### user_ability_profiles

| 字段 | 类型建议 | 说明 |
|---|---|---|
| id | string/uuid | 能力画像 ID。 |
| user_id | string/uuid | 所属用户。 |
| level | enum/string | `unknown / beginner / normal / strong`。 |
| endurance_score | decimal/null | 耐力评分，0-1。 |
| climb_score | decimal/null | 爬坡能力评分，0-1。 |
| recent_max_distance_km | decimal/null | 近期最大完成距离。 |
| recent_max_elevation_gain_m | decimal/null | 近期最大完成爬升。 |
| activity_count | integer | 已导入活动数量。 |
| confidence | enum/string | `unknown / low / medium / high`。 |
| generated_from_activity_track_ids | JSON | 画像基于哪些活动轨迹生成。 |
| created_at | datetime | 创建时间。 |
| updated_at | datetime | 更新时间。 |

关系：

```text
users 1:N activity_tracks
users 1:1 user_ability_profiles
users 1:N trip_plans
users 1:N route_plan_snapshots
users 1:N route_assets
```

设计边界：

```text
activity_tracks 是用户已完成活动记录，用于能力画像。
route_assets 是线路资产，用于线路库和规划。
二者不能混用。
```
