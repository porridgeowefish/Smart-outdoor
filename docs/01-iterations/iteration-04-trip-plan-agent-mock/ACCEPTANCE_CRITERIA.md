# Acceptance Criteria

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: product acceptance and tests.

```text
聊天页发送消息后能看到 assistant 回复
后端 SSE 事件回放接口可调用，但前端未接入，真实流式体验 pending
信息充分时，前端从 POST /api/trip-plans/messages 响应体的 candidate_routes 渲染最多 3 张候选线路卡片
候选线路必须来自数据库线路资产，不能由 LLM 编造
天气 / 交通 / Web 证据查询发生在 top 3 候选确定之后
点击卡片能看到候选详情
候选详情可以通过 route.route_id 进入线路详情
候选详情不会自动创建 snapshot
信息不足时 Agent 能自然追问
能回看 TripPlan 列表和某个 TripPlan 的消息历史
不能访问其他用户的 TripPlan、AgentRun 或候选详情
```
