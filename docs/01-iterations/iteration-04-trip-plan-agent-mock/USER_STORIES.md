# User Stories

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: this iteration plus implemented tests.

## US-04.1 发送对话消息

作为用户，我希望在“出去走走”发送自然语言需求，以便系统创建规划对话并启动 AgentRun。

验收要点：

```text
没有 trip_plan_id 时创建新 trip_plan
有 trip_plan_id 时追加消息
每条用户消息创建一个 agent_run
closed trip_plan 不能追加
返回 assistant_message
信息不足时 run_status=waiting_user
信息充分时 run_status=succeeded，并在 POST /api/trip-plans/messages 响应体中返回后端规则召回的最多 3 条 candidate_routes
候选线路来自数据库 route_assets，不由 LLM 编造
```

## US-04.2 查看规划列表和会话历史

作为用户，我希望能回看自己的 TripPlan 和消息历史，以便回到一次规划继续查看。

验收要点：

```text
GET /api/trip-plans 只返回当前用户的 trip_plan
GET /api/trip-plans/{trip_plan_id}/messages 返回 messages
会话历史返回最近一次 AgentRun 的 candidate_routes，供前端恢复候选卡片
不能读取其他用户的 trip_plan
```

## US-04.3 接收 Agent 流式事件

作为用户，我希望看到 Agent 的流式回复和状态变化，以便知道系统正在处理我的需求。

验收要点：

```text
后端 SSE 返回标准 event/data 行格式
支持 phase_changed / message.delta / message.completed
支持 run.waiting_user / candidate_routes.updated / run.completed
当前 SSE 从 agent_runs.events_json 重放已生成事件
前端尚未接入 SSE，真实实时流式 pending
```

## US-04.4 查看候选线路详情

作为用户，我希望点击候选卡片查看推荐理由、风险和证据，以便判断这条线路是否值得保存。

验收要点：

```text
详情返回 route
详情返回 planning_detail
详情返回 evidence
evidence 在 top 3 候选确定后查询
当前 evidence 不参与排序
详情返回 score_breakdown / advantage_tags / recommendation_reason
点击详情不创建 snapshot
candidate_id 来自消息响应或会话历史响应中的 candidate_routes
可以通过 route.route_id 跳转到线路资产详情
```
