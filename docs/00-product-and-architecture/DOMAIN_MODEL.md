# 领域模型

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: migrated from PRD, US-01/02/03 design docs, and ER diagram.

## 核心领域对象

```text
User
用户身份与资料。

TripPlan
一次由对话触发的规划工作区。

AgentRun
一次用户消息触发的 Agent 后台运行。

RouteAsset
线路资产，用于线路库、搜索、规划和 Agent 推荐。

RouteFile
线路原始轨迹文件，例如 KML / GPX / GeoJSON。

RouteAnalysisSnapshot
线路解析后的客观技术指标和 track_geojson。

TripPlanCandidateRoute
某个 TripPlan 中 Agent 推荐过的一条候选线路。

RoutePlanSnapshot
用户保存到“我的规划”的方案快照。

ActivityTrack
用户已完成活动轨迹，用于能力画像。

UserAbilityProfile
用户能力画像，用于推荐时的人线匹配。
```

## 最重要的边界

### route_asset 与 activity_track 不得混用

```text
route_asset
线路资产：我想走 / 我上传来规划 / 线路库中的可规划对象。

activity_track
活动记录：我已经走过 / 我的运动记录 / 用来证明我的能力。
```

不能混用的原因：

```text
能力画像污染
隐私语义不同
UI 心智不同
扩展字段不同
```

### 候选与快照不同

```text
TripPlanCandidateRoute
Agent 在某次规划语境下推荐过的候选。

RoutePlanSnapshot
用户明确点击保存后沉淀下来的规划快照。
```

点击候选详情不创建 snapshot。只有保存到“我的规划”才创建 snapshot。

### 原始轨迹与渲染轨迹分离

```text
route_files
保存原始 KML / GPX / GeoJSON。

route_analysis_snapshots.track_geojson
保存简化 GeoJSON，用于地图渲染。

route_analysis_snapshots 指标字段
保存距离、爬升、海拔、坡度等，用于筛选、推荐和详情展示。
```

## manual_tags 的边界

manual_tags 是线路补充语义，不是事实证据。

可用于：

```text
线路详情展示
线路搜索筛选
Agent 偏好召回
优势标签生成
```

不能替代：

```text
轨迹指标
天气 API
交通 API
外部证据
近期路况
```

