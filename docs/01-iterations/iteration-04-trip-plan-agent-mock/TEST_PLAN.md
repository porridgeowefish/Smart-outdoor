# Test Plan

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests under `backend/tests/trip_plans/`.

## Service / Unit

- [US-04.1] 信息不足 → run_status=waiting_user，不进入 route_retrieval。
- [US-04.1] 信息充分 → 进入 route_retrieval，从可见 route_assets 排序召回，候选最多 3 条。
- [US-04.1] route_retrieval 仅召回 public 线路 + 本人 private 线路且须有 analysis snapshot。
- 天气 / 交通 / Web 证据只对 top 3 候选查询；当前固定 evidence_score，真实证据不进排序。
- [US-04.1] assistant 消息最终落库到 trip_plan_messages。
- [US-04.4] candidate detail 使用 candidate_routes[].candidate_id 获取，返回 route + planning_detail + evidence。

## API

- [US-04.1] 首条消息（无 trip_plan_id）→ 创建新 trip_plan。
- [US-04.1] 后续消息（带 trip_plan_id）→ 追加到同一 trip_plan。
- [US-04.1] 每条用户消息创建一个 agent_run。
- [US-04.1] 空 content / extra 字段 → Pydantic 422。
- [US-04.1] 不存在 trip_plan_id → 404 TRIP_PLAN_NOT_FOUND。
- [US-04.1] closed trip_plan → 400 TRIP_PLAN_CLOSED。
- [US-04.1] 信息充分时 POST /api/trip-plans/messages 响应体含数据库规则召回的最多 3 条 candidate_routes。
- [US-04.2] GET /api/trip-plans 只返回当前用户列表。
- [US-04.2] GET /api/trip-plans/{id}/messages 返回消息和最近一次候选。
- [US-04.3] GET /api/agent-runs/{id}/events 返回 text/event-stream，回放 events_json。
- [US-04.3] SSE 当前只验证后端事件回放；前端接入 pending。
- [US-04.4] GET candidate detail 返回 route + planning_detail + evidence。

## 权限

- 不能读取其他用户 trip_plan conversation。
- 不能读取其他用户 agent_run events。
- 不能读取其他用户 candidate detail。

## 失败路径

- [US-04.1] 漏传 trip_plan_id 继续对话 → 创建新 trip_plan（新上下文，非继续），须有测试明确覆盖。
- workflow 异常 → POST /api/trip-plans/messages 返回 500 AGENT_ERROR。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test_iter4_tmp.db'
pytest backend/tests/trip_plans/test_trip_plan_agent_api.py backend/tests/trip_plans/test_agent_workflow_units.py backend/tests/trip_plans/test_route_retrieval.py
```

## 备注

- 真实流式推送（边执行边生成事件）当前未实现，SSE 测试只覆盖回放路径；前端 SSE 接入见 TODO-04.0。
- `client_context` 当前 Request `extra=forbid`，不接受；待办见 TODO-04.1。
