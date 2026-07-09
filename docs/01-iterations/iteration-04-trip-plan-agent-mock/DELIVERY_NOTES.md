# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes for Iteration 04.

## 交付内容

- 新增 TripPlan + Agent workflow 最小可运行闭环：trip_plans / trip_plan_messages / agent_runs / trip_plan_candidate_routes 四表 + ORM 模型。
- 实现 `POST /api/trip-plans/messages` 合并接口（新建 / 继续由 trip_plan_id 区分），同步执行 workflow 并返回 assistant_message / run_status / candidate_routes。
- 实现 route_retrieval：从数据库可见 route_assets 规则召回排序（ability / preference / metrics + 固定 evidence_score），最多 3 条候选，不由 LLM 编造。
- 实现证据查询：天气 / 交通 / Web 只对 top 3 候选执行，进入 candidate detail 与 assistant 文案，不参与排序。
- 实现 `GET /api/trip-plans`、`GET /api/trip-plans/{id}/messages`、`GET /api/trip-plans/{id}/candidate-routes/{candidate_id}`、`GET /api/agent-runs/{id}/events`（SSE 回放）。
- 新增测试：`backend/tests/trip_plans/test_trip_plan_agent_api.py`、`test_agent_workflow_units.py`、`test_route_retrieval.py`、`test_evaluator.py`。
- 落地 commit：`a6bfce7 feat: Agent workflow + cloud deployment`（随 MVP `b5f0f73` 全量代码引入）。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test_iter4_tmp.db'
pytest backend/tests/trip_plans/
```

结果：历史迭代，未记录具体通过数；测试文件随 MVP 引入，当前仓库可运行。

## 遗留风险

- SSE 当前为 workflow 完成后的 events_json 回放，非真实边执行边推送；前端尚未接入。
- evidence 不参与召回排序，固定 evidence_score=0.08；真实天气/交通/Web 证据只进详情与文案。
- `candidate_routes.updated` 事件当前只承载候选摘要，非完整候选卡片数据来源。
- `POST /api/trip-plans/messages` Request `extra=forbid`，不接受 `client_context`，跨时区 / 多语言场景下相对时间解析依赖服务端默认。
- 漏传 trip_plan_id 继续对话会创建新 TripPlan，需前端状态机严格保存当前 trip_plan_id。

## 对齐与决策

### 召回与证据分工（随 MVP 定稿）

```text
LLM 负责 context_state 抽取与回复文案生成，不直接生成路线。
路线召回由后端从 route_assets + route_analysis_snapshots 规则召回排序。
evidence（天气 / 交通 / Web）查询发生在 top 3 候选确定之后，不参与排序。
```

### Route Retrieval / Evidence 时序

POST `/api/trip-plans/messages` 的候选生成顺序：

```text
1. LLM 抽取 / 合并 context_state
2. 判断信息充分度
3. 从数据库可见 route_assets 召回线路
4. 按 ability / preference / metrics / 固定 evidence_score 排序
5. 取 top 3
6. 对 top 3 查询天气 / 交通 / Web 证据
7. 写入 trip_plan_candidate_routes
8. 返回 response.candidate_routes 给前端渲染候选卡片
```

### SSE 现状

```text
已实现：GET /api/agent-runs/{id}/events 把 events_json 转 text/event-stream。
未完成：前端未调用；非边执行边推送，而是 workflow 完成后回放。
前端主链路：POST /api/trip-plans/messages 响应体的 candidate_routes。
```

## 暴露的权衡

- 沿用 messages 合并接口（trip_plan_id 区分新建/继续）而非独立“新建对话”接口，减少接口数量，代价是前端必须严格保存 trip_plan_id。
- evidence 固定评分而非真实参与排序：换取召回稳定性与可解释性，代价是真实路况/天气不直接影响排序。
- SSE 回放而非真实流式：换取实现简洁，代价是前端流式体验 pending。

> 契约级规则（端点、字段、错误码）见 API_CONTRACT；数据结构见 DATABASE_DESIGN；用例见 TEST_PLAN。后续待办（SSE 接入、client_context、trip_plan_id 契约硬化）见 TODO.md，不在本文件重复。
