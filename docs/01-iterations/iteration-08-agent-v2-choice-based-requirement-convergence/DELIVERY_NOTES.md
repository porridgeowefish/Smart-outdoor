# Delivery Notes

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: implementation notes after this slice lands.

## 2026-05-20 对齐阶段

当前只完成文档对齐，尚未进入代码实现。

已对齐内容：

```text
Iteration 08 的核心闭环是同一 TripPlan 会话内多次选择、持续累积 context_state、条件满足后生成推荐。
推荐生成后，用户仍可追问、解释、修改条件或要求换推荐。
ask_user_choice 作为领域工具调用表达待确认问题。
选择结果直接写入 context_state，用来替代对应字段上的 AI 倾向判断。
字段可信度优先级为 user_choice > user_explicit_text > ai_extracted。
context_state 字段分为基础核心字段、场景化阻塞字段、偏好字段和元字段。
2026-05-22 对齐反馈修正：基础核心字段不包含 ability_hint，能力匹配主要来自用户能力画像；ability_hint 只作为本次强度偏好或覆盖项。
2026-05-22 对齐反馈修正：充分条件采用 scenario_based，风险场景需要确认 terrain_tolerance 或 safety_priority。
2026-05-22 对齐反馈修正：一轮 ask_user_choice 最多 3 个问题，但前端逐步呈现，不一次性全部展开。
2026-05-22 对齐反馈修正：本轮控件只包含 single_choice、multi_choice、text/custom，不包含 range。
2026-05-22 对齐反馈修正：choice_request_id 使用独立 UUID，confirmed_context 返回可展示摘要，历史恢复最近未完成选择卡。
自然语言入口复用 POST /api/trip-plans/messages。
选择结果入口采用 POST /api/trip-plans/{trip_plan_id}/choice-results。
choice_request 和 choice_result 需要结构化落库，支持历史会话恢复。
HTTP 实现中 waiting_user AgentRun 不长期挂起；选择提交后创建新的 AgentRun 继续推进。
```

尚未实现：

```text
Agent workflow 选择卡生成。
前端选择栏 UI。
OpenAPI 与前端类型生成。
```

## 2026-05-23 后端选择式收敛第一切片

已实现内容：

```text
TripPlanMessage 增加 content_type 和 payload，用于结构化保存 choice_request / choice_result。
init_db 增加 Iteration 08 兼容列补齐逻辑。
TripPlanMessageResponse 增加 content_type 和 payload。
TripPlanMessagePostResponse 增加 choice_request、confirmed_context、missing_fields。
POST /api/trip-plans/messages 在信息不足时返回 ask_user_choice 结构化 choice_request。
新增 POST /api/trip-plans/{trip_plan_id}/choice-results。
choice-results 写入 role=user、content_type=choice_result 的消息记录。
choice-results 直接合并到 trip_plans.context_state，并将字段来源标为 user_choice。
sufficiency_check 改为基础核心字段 + 风险场景阻塞字段。
ability_hint 不再作为默认基础核心字段。
GET /api/trip-plans/{trip_plan_id}/messages 返回历史消息的 content_type 和 payload。
closed trip_plan 同时拒绝自然语言消息和 choice-results。
```

验证：

```text
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest tests/trip_plans/test_agent_workflow_units.py tests/trip_plans/test_trip_plan_agent_api.py
17 passed

$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest
111 passed
```

仍待实现：

```text
Agent real provider 输出 choice_request 的严格 schema 校验与降级。
前端选择栏 UI。
前端 OpenAPI 类型生成与 API client 对接。
前端逐题呈现 / 历史恢复 / 选择摘要展示。
choice_request 过期或被新一轮问题替代时的错误语义。
部分答案提交策略。
```

## 2026-05-23 choice_request 活跃性规则收敛

对齐并实现：

```text
本轮不支持部分答案提交；前端逐题呈现，后端整组接收。
后端提交校验要求 answers 覆盖本次 choice_request 全部 questions。
choice_request 不设置 TTL，避免破坏历史会话异步恢复。
后端按 trip_plan_messages 时间线判断当前 active choice_request。
已回答、被后续 choice_request 替代或非最新未回答的 choice_request 返回 CHOICE_REQUEST_NOT_ACTIVE。
CHOICE_REQUEST_NOT_ACTIVE 使用 HTTP 409。
前端历史会话恢复时，仅最近一条 active choice_request 恢复为可交互选择卡。
```

验证：

```text
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest tests/trip_plans/test_agent_workflow_units.py tests/trip_plans/test_trip_plan_agent_api.py
```
