# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: backend tests.

## API 测试

```text
第一条消息创建 trip_plan
后续消息追加到同一个 trip_plan
每条用户消息创建 agent_run
空消息由 Pydantic 返回 422
不存在 trip_plan 返回 TRIP_PLAN_NOT_FOUND
closed trip_plan 返回 TRIP_PLAN_CLOSED
信息充分时 POST /api/trip-plans/messages 响应体包含数据库规则召回的最多 3 条 candidate_routes
GET /api/trip-plans 返回当前用户列表
GET /api/trip-plans/{trip_plan_id}/messages 返回消息和候选
不能读取其他用户 trip_plan conversation
SSE 返回必要事件
SSE 当前只验证后端事件回放
前端 SSE 接入 pending
不能读取其他用户 agent_run events
candidate detail 返回 route + planning_detail + evidence
不能读取其他用户 candidate detail
```

## Workflow 测试

```text
信息不足返回 run.waiting_user
信息充分进入 route_retrieval
route_retrieval 从可见 route_assets 中排序召回
候选最多 3 条
天气 / 交通 / Web 证据只对 top 3 候选查询
当前证据不参与排序
candidate detail 使用 candidate_routes[].candidate_id 获取详情
assistant 消息最终落库
```
