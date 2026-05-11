# MVP 实施切片计划

## 1. 开发原则

本项目下午编码采用：

```text
切片开发 + 测试驱动开发
```

核心纪律：

```text
1. 按用户闭环切片
每个 slice 都必须跑通一个真实用户动作。

2. 每个 slice 先写测试
先写 API / service / parser 的关键测试，再写实现。

3. 每个 slice 完成后立即验收
不等全部写完再测。

4. 不做横向大工程
不要先铺满 model / repository / service 空架子。

5. 允许 mock 外部依赖
LLM / Tavily / 天气 / 高德可以先 mock 或降级，保证主链路跑通。

6. 严禁旧项目迁移污染
只复用明确低耦合 utils，例如 geo.py。
```

完成标准：

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
没有无用抽象
```

## 2. Slice 1：Auth + User

目标：用户可以注册、登录、获取自己的用户信息。

接口：

```text
POST /api/auth/register
POST /api/auth/login
GET /api/me
PATCH /api/me
```

测试优先：

```text
注册成功
重复用户名/邮箱失败
登录成功返回 JWT
密码错误失败
GET /api/me 需要 Authorization
PATCH /api/me 只能改 nickname / avatar_url
```

验收：

```text
前端能注册登录
localStorage 保存 token
后续请求自动带 Bearer token
个人中心能看到昵称和头像
```

## 3. Slice 2：Route Upload + Parser

目标：用户可以上传 GPX/KML/GeoJSON，系统解析并生成线路资产。

接口：

```text
POST /api/routes/upload
```

涉及数据：

```text
route_assets
route_files
route_analysis_snapshots
```

测试优先：

```text
支持合法文件类型
拒绝非法文件类型
解析距离、爬升、起终点
生成 track_geojson
manual_tags 正确保存
parse_status 成功为 parsed
解析失败为 failed 或返回 TRACK_PARSE_FAILED
```

验收：

```text
上传一条轨迹后数据库有 route_asset
有 route_file 原始文件记录
有 route_analysis_snapshot 指标和 track_geojson
```

## 4. Slice 3：Route List + Detail

目标：线路 Tab 可以展示线路卡片和详情，详情能提供地图渲染数据。

接口：

```text
GET /api/routes
GET /api/routes/{route_id}
```

测试优先：

```text
默认返回 public + 当前用户 private
不返回其他用户 private
支持 tags 筛选
详情返回 analysis
详情返回 track.geojson
详情返回 primary_file
权限校验正确
```

验收：

```text
前端能看到线路卡片
点击进入详情
详情页能拿到 GeoJSON 轨迹用于地图渲染
```

## 5. Slice 4：TripPlan + Agent Mock

目标：出去走走可以发送消息，创建 trip_plan，建立 SSE，返回 mock 推荐 3 条线路。

接口：

```text
POST /api/trip-plans/messages
GET /api/agent-runs/{agent_run_id}/events
GET /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}
```

测试优先：

```text
第一条消息创建 trip_plan
后续消息追加到同一个 trip_plan
每条用户消息创建 agent_run
closed trip_plan 不允许追加消息
SSE 返回 7 类契约事件中的必要事件
mock route_retrieval 返回 3 条 candidate_routes
candidate detail 返回 route + planning_detail + evidence
```

验收：

```text
聊天页发送消息后能看到流式回复
能看到 3 张候选线路卡片
点击卡片能看到候选详情
```

## 6. Slice 5：Snapshot / 我的规划

目标：用户可以把候选线路保存到我的规划，并查看快照列表和详情。

接口：

```text
POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save
GET /api/my/route-plan-snapshots
GET /api/my/route-plan-snapshots/{snapshot_id}
```

测试优先：

```text
保存 candidate 创建 route_plan_snapshot
同一个 candidate_id 不能重复保存
我的规划列表只返回当前用户 snapshot
详情返回保存时刻的 route_summary / planning_detail / evidence
详情支持 continue_trip_plan_id
```

验收：

```text
候选详情页点击保存
我的规划出现卡片
点击卡片进入快照详情
```

## 7. Slice 6：Ability Profile

目标：个人中心可以上传完成轨迹并生成基础能力画像。

接口：

```text
POST /api/me/activity-tracks/upload
GET /api/me/ability-profile
```

测试优先：

```text
上传完成轨迹生成 activity_track
不会创建 route_asset
解析距离和爬升
生成 user_ability_profile
activity_count 正确递增
confidence 按规则变化
```

验收：

```text
个人中心上传一条完成轨迹
页面显示耐力、爬坡能力、最大距离、最大爬升、可信度
```

## 8. 外部依赖策略

下午 Demo 阶段：

```text
LLM 可先 mock。
Tavily 可先 mock。
QWeather 可先 mock 或降级。
AMap 可先 mock 或只接 driving。
```

硬规则：

```text
mock 和 real 必须走同一个接口类型。
前端不能因为 mock/real 切换而改页面代码。
后端通过环境变量切换 provider。
```

推荐环境变量：

```text
USE_MOCK_LLM=true
USE_MOCK_WEATHER=true
USE_MOCK_AMAP=true
USE_MOCK_SEARCH=true
```

## 9. 契约驱动前后端对接

后端必须生成 OpenAPI schema。
前端必须从 OpenAPI schema 生成 TypeScript 类型和 API Client。
前端页面禁止手写接口类型。

推荐流程：

```text
后端 Pydantic Schema
↓
FastAPI 自动生成 /openapi.json
↓
前端用 openapi-typescript 生成 types
↓
前端用统一 apiClient 调用
↓
mock/real 通过环境变量切换 baseURL 或 MSW handler
```

前端切换：

```text
VITE_USE_MOCK_API=true
```

当为 true：

```text
前端请求进入 MSW mock handlers。
```

当为 false：

```text
前端请求进入真实后端 /api。
```

要求：

```text
mock response 必须从 OpenAPI 类型派生。
mock 数据不能随便写字段。
真实后端 Response 必须匹配 OpenAPI。
```
