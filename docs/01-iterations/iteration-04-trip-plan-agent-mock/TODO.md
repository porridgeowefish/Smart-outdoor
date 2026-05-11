# TODO

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: implementation tasks discovered while syncing current code to docs.

本文件记录当前实现与合理产品契约之间的待办。完成任一 TODO 后，必须同步更新对应 Pydantic Schema、OpenAPI、测试和本迭代文档。

## 已确认共识

```text
路线召回不由 LLM 生成。
LLM 负责 context_state 抽取和回复文案生成。
候选线路来自数据库 route_assets + route_analysis_snapshots。
天气 / 交通 / Web 证据查询发生在 top 3 候选确定之后。
当前 evidence 不参与路线排序。
```

## TODO-04.0 接入真实 SSE 流式体验

### 背景

当前后端已实现：

```text
GET /api/agent-runs/{agent_run_id}/events
把 agent_runs.events_json 转为 text/event-stream 返回。
```

但这只是事件回放：

```text
POST /api/trip-plans/messages 先同步跑完整个 workflow
workflow 完成后 events_json 已经写入 DB
前端目前没有调用 SSE 接口
```

### 需要完成

```text
前端接入 /api/agent-runs/{agent_run_id}/events
根据 run.phase_changed 更新进度
根据 message.delta / message.completed 更新 assistant 文本
根据 candidate_routes.updated 更新候选状态
明确 SSE 和 POST JSON 响应的职责边界
后端如需真实边执行边推送，需要把 workflow 从同步返回改为可流式产生事件
```

### 当前限制

```text
candidate_routes.updated 当前不是完整候选卡片数据来源。
候选卡片主数据仍来自 POST /api/trip-plans/messages 响应体 candidate_routes。
```

### 完成后必须同步的文档

```text
docs/01-iterations/iteration-04-trip-plan-agent-mock/API_CONTRACT.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/USER_STORIES.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/TEST_PLAN.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/ACCEPTANCE_CRITERIA.md
```

## TODO-04.1 支持 client_context

### 背景

历史 API 契约中 `POST /api/trip-plans/messages` 支持：

```json
{
  "trip_plan_id": null,
  "content": "我周末想从成都出发看雪山",
  "client_context": {
    "timezone": "Asia/Shanghai",
    "locale": "zh-CN"
  }
}
```

当前实现的 `TripPlanMessageRequest` 只接受：

```json
{
  "trip_plan_id": null,
  "content": "..."
}
```

并且设置了 `extra="forbid"`。前端如果传 `client_context` 会收到 `422`。

### 为什么需要做

`client_context` 用于补充客户端环境，帮助 Agent 稳定解析相对时间和展示偏好。

最低价值：

```text
timezone
用于把“明天、周末、早上”等相对时间解析到用户本地时区。

locale
用于语言、日期格式、单位和默认文案偏好。
```

没有这个字段时，Agent 只能靠服务端默认环境推断，容易在跨时区、日期边界和多语言场景中出错。

### 建议实现

1. 在 `backend/app/features/trip_plans/schemas.py` 增加 Pydantic V2 模型。

```text
TripPlanClientContext
- timezone: str | None = None
- locale: str | None = None
```

2. 在 `TripPlanMessageRequest` 中增加：

```text
client_context: TripPlanClientContext | None = None
```

3. 在 service 层把 `client_context` 合并进 `trip_plans.context_state`，至少保存：

```text
client_timezone
client_locale
```

4. 后续 LLM context extraction / time parsing 使用该 context。MVP 可以先持久化，不必一次性完成复杂时间解析。

### 验收要求

```text
POST /api/trip-plans/messages 接受 client_context
client_context 缺失时仍兼容旧请求
client_context 额外字段不污染业务状态
timezone / locale 被保存到 trip_plan.context_state 或等价结构
/openapi.json 暴露 client_context schema
新增 API 测试覆盖带 client_context 的请求
```

### 完成后必须同步的文档

```text
docs/01-iterations/iteration-04-trip-plan-agent-mock/API_CONTRACT.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/USER_STORIES.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/TEST_PLAN.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/ACCEPTANCE_CRITERIA.md
```

完成后需要把 `API_CONTRACT.md` 中“当前实现不接受 client_context”改为正式请求字段说明。

## TODO-04.2 强化 TripPlan 合并消息接口的上下文契约

### 背景

当前 `POST /api/trip-plans/messages` 通过 request body 中的可选 `trip_plan_id` 区分两种行为：

```text
trip_plan_id = null
创建新的 TripPlan，上下文从空开始。

trip_plan_id = "tp_xxx"
继续已有 TripPlan，在该 TripPlan 的 context_state 和历史消息上追加。
```

这个设计可以工作，也可以少一个“新建对话”接口，MVP 保留当前合并接口。关键是文档、测试和前端状态管理必须写硬。否则前端如果在后续对话中漏传 `trip_plan_id`，后端会创建一个新的 TripPlan，用户会以为在继续同一个对话，实际上下文已经断开。

### 当前上下文组织方式

```text
TripPlan.context_state
保存一个规划工作区的结构化上下文。

trip_plan_messages.trip_plan_id
把用户/assistant 消息归属到某个 TripPlan。

agent_runs.trip_plan_id
把一次 Agent 后台运行归属到某个 TripPlan。

trip_plan_candidate_routes.trip_plan_id
把候选线路归属到某个 TripPlan。
```

服务端依赖 `trip_plan_id` 区分上下文。只要前端正确传回 `trip_plan_id`，上下文可以区分开。

### 契约要求

保留当前接口：

```text
POST /api/trip-plans/messages
```

请求语义：

```text
trip_plan_id = null / 缺失
创建新的 TripPlan，上下文从空开始。

trip_plan_id = "tp_xxx"
继续已有 TripPlan，在该 TripPlan 的 context_state 和历史消息上追加。
```

前端进入已有 TripPlan 对话后，发送任何后续消息都必须携带当前 `trip_plan_id`。如果漏传，后端创建新 TripPlan，这是新上下文，不是继续上下文。

### 验收要求

```text
第一条消息不传 trip_plan_id 时创建新 TripPlan
后续消息传同一个 trip_plan_id 时追加到同一个 TripPlan
后续消息不传 trip_plan_id 时创建新的 TripPlan，并有测试明确覆盖
传不存在的 trip_plan_id 时返回 TRIP_PLAN_NOT_FOUND
不能追加到其他用户的 TripPlan
closed TripPlan 不能追加
前端状态必须保存当前 trip_plan_id
```

### 完成后必须同步的文档

```text
docs/01-iterations/iteration-04-trip-plan-agent-mock/API_CONTRACT.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/USER_STORIES.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/TEST_PLAN.md
docs/01-iterations/iteration-04-trip-plan-agent-mock/ACCEPTANCE_CRITERIA.md
```

如果这个契约影响前端调用，还必须同步：

```text
前端 OpenAPI 生成类型
前端 apiClient 调用
mock handler 类型
```

并在 `API_CONTRACT.md` 中明确 `trip_plan_id` 的两种语义，以及前端继续对话必须传回 `trip_plan_id`。
