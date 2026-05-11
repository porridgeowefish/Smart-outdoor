# MVP 路线图

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: migrated from `docs/99-archive/backend-docs-legacy/MVP_IMPLEMENTATION_SLICES.md`; detailed delivery scope lives in `docs/01-iterations/`.

## 开发原则

```text
切片开发
测试驱动开发
契约驱动前后端对接
Mock / Real 可切换
不做横向大工程
不迁移旧项目大块代码
```

## 迭代顺序

### Iteration 01 Auth + User

用户可以注册、登录、获取和更新自己的基础资料。

关键接口：

```text
POST /api/auth/register
POST /api/auth/login
GET /api/me
PATCH /api/me
```

### Iteration 02 Route Upload + Parser

用户上传 GPX/KML/GeoJSON，系统解析并生成线路资产。

关键接口：

```text
POST /api/routes/upload
```

### Iteration 03 Route List + Detail

线路 Tab 展示线路卡片和详情，详情提供地图渲染数据。

关键接口：

```text
GET /api/routes
GET /api/routes/{route_id}
```

### Iteration 04 TripPlan + Agent Mock

出去走走可以发送消息，创建 trip_plan，建立 SSE，返回 mock 推荐 3 条线路。

关键接口：

```text
POST /api/trip-plans/messages
GET /api/agent-runs/{agent_run_id}/events
GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}
```

### Iteration 05 Snapshot / 我的规划

用户可以把候选线路保存到我的规划，并查看快照列表和详情。

关键接口：

```text
POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save
GET /api/my/route-plan-snapshots
GET /api/my/route-plan-snapshots/{snapshot_id}
```

### Iteration 06 Ability Profile

个人中心上传完成轨迹并生成基础能力画像。

关键接口：

```text
POST /api/me/activity-tracks/upload
GET /api/me/ability-profile
```

## 每轮完成定义

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
契约类型已生成
mock/real 切换不改页面代码
没有无用抽象
文档已同步
```

