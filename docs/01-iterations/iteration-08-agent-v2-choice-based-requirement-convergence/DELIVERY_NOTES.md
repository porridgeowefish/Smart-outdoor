# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes after this slice lands.

## 交付内容

- TripPlanMessage 新增 `content_type` 和 `payload` 列，结构化保存 choice_request / choice_result；init_db 含 Iteration 08 兼容列补齐逻辑。
- TripPlanMessageResponse 新增 `content_type` 和 `payload`；TripPlanMessagePostResponse 新增 `choice_request` / `confirmed_context` / `missing_fields`。
- POST /api/trip-plans/messages 在信息不足时返回结构化 `choice_request`。
- 新增 POST /api/trip-plans/{trip_plan_id}/choice-results：写入 role=user、content_type=choice_result 消息，合并到 trip_plans.context_state，字段来源标为 user_choice。
- sufficiency_check 改为基础核心字段 + 风险场景阻塞字段；ability_hint 不再作为默认基础核心字段。
- GET /api/trip-plans/{trip_plan_id}/messages 返回历史消息的 content_type 和 payload。
- closed TripPlan 同时拒绝自然语言消息和 choice-results。
- choice_request 活跃性规则实现：不支持部分答案提交、按时间线判断 active、409 CHOICE_REQUEST_NOT_ACTIVE、404 CHOICE_REQUEST_NOT_FOUND。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest tests/trip_plans/test_agent_workflow_units.py tests/trip_plans/test_trip_plan_agent_api.py
```

```text
17 passed
```

```powershell
$env:DATABASE_URL='sqlite:///./test_iter8_tmp.db'; pytest
```

```text
111 passed
```

## 遗留风险

- Agent real provider 输出 choice_request 的严格 schema 校验与降级尚未实现。
- 前端选择栏 UI、OpenAPI 类型生成与 API client 对接、逐题呈现 / 历史恢复 / 选择摘要展示尚未实现。
- choice_request 过期或被新一轮问题替代时的错误语义已落地基础（409），但部分答案提交策略仍待定。
- 场景化 sufficiency 规则的风险触发表目前由关键词集合（雪/冰/野路/亲子/新手/安全/危险）驱动，细分场景覆盖待后续迭代加强。
- missing_fields 是否固定为枚举尚未最终确定。

## 对齐与决策

### 2026-05-20 对齐阶段

Iteration 08 的核心闭环定为同一 TripPlan 会话内多次选择、持续累积 context_state、条件满足后生成推荐。推荐生成后用户仍可追问、解释、修改条件或要求换推荐。ask_user_choice 作为领域工具调用表达待确认问题。选择结果直接写入 context_state，用来替代对应字段上的 AI 倾向判断。字段可信度优先级定为 `user_choice > user_explicit_text > ai_extracted`。

```text
context_state 字段分为基础核心字段、场景化阻塞字段、偏好字段和元字段。
HTTP 实现中 waiting_user AgentRun 不长期挂起；用户提交选择后创建新的 AgentRun 继续推进。
choice_request 和 choice_result 需要结构化落库，支持历史会话恢复。
```

### 2026-05-22 对齐反馈修正

```text
基础核心字段不包含 ability_hint；能力匹配主要来自用户能力画像，ability_hint 只作为本次强度偏好或覆盖项。
充分条件采用 scenario_based：基础字段满足后，若涉及雪、冰雪路、野路、亲子等风险场景，还需确认 terrain_tolerance 或 safety_priority。
一轮 ask_user_choice 最多 3 个问题，但前端逐步呈现，不一次性全部展开。
本轮控件只含 single_choice / multi_choice / text-custom，不含 range。
choice_request_id 使用独立 UUID；confirmed_context 返回可展示摘要；历史恢复最近未完成选择卡。
```

入口决策：

```text
自然语言继续使用 POST /api/trip-plans/messages。
选择结果使用 POST /api/trip-plans/{trip_plan_id}/choice-results。
选择结果不伪装成自然语言文本，直接作为结构化 tool result 写入 context_state。
```

### 2026-05-23 choice_request 活跃性规则收敛

```text
本轮不支持部分答案提交；前端逐题呈现，后端整组接收。
后端提交校验要求 answers 覆盖本次 choice_request 全部 questions。
choice_request 不设 TTL，避免破坏历史会话异步恢复。
后端按 trip_plan_messages 时间线判断当前 active choice_request。
已回答、被后续 choice_request 替代或非最新未回答的 choice_request 返回 CHOICE_REQUEST_NOT_ACTIVE（HTTP 409）。
choice_request_id 不存在或不属于当前用户 / TripPlan 返回 CHOICE_REQUEST_NOT_FOUND（HTTP 404）。
前端历史会话恢复时，仅最近一条 active choice_request 恢复为可交互选择卡。
```

### context_state tiering 与可信度原则（设计理由，不入契约）

选择题不是旁路信息，而是对 context_state 的高可信写入，目的是替代不稳定的 AI 倾向判断。写入优先级：

```text
1. 用户在选择题中的显式选择或自定义输入。
2. 用户自然语言中的显式修改，例如“不要自驾了，改公共交通”。
3. AI 从自然语言中抽取出的低置信度倾向。
```

同字段已由用户选择确认后，AI 后续抽取不能静默覆盖；只有用户再次明确选择或明确用自然语言修改时才能覆盖。用户再次提交 choice-result 可覆盖旧 user_choice；用户自然语言明确修改时可覆盖 user_choice，但来源须重标为 user_explicit_text。

context_state 白名单分层（数据契约见 DATABASE_DESIGN；此处保留分层理由）：

```text
基础核心字段（直接影响能否进入推荐）：activity_goal / departure_area / time_window / transport_hint
场景化阻塞字段（仅风险场景影响推荐）：terrain_tolerance / safety_priority
偏好字段（影响选择卡、召回加权、扣分、解释，默认不阻塞）：preference_tags / avoid_tags / scenery_preferences / supply_requirement / ability_hint
元字段（可信度、展示、调试）：confirmed_fields / missing_fields / field_sources
暂不纳入本轮充分条件：current_location / communication_requirement / emergency_requirement / budget_hint / group_profile
```

风险场景触发说明：terrain_tolerance / safety_priority 默认不阻塞所有推荐；当 activity_goal、preference_tags、avoid_tags 或用户原话涉及雪、冰雪路、野路、亲子、新手、安全优先等风险场景时，至少需确认其一。

### ask_user_choice 交互模型（设计理由，不入契约）

```text
借鉴 Claude Code / Claude Agent SDK 的 AskUserQuestion 模式：Agent 需要补充信息时通过工具调用产出结构化问题，宿主 UI 展示选择栏，用户选择后工具调用返回答案，Agent 基于答案继续执行。
项目内不绑定 Claude Code SDK，抽象为领域工具 ask_user_choice。
ask_user_choice 是 workflow 中的交互暂停点，不是最终回复。
返回后同一 AgentRun / TripPlan 继续推进，更新 context_state；多次 ask_user_choice 可在同一会话发生。
```

第一轮选择卡策略（设计理由）：

```text
第一轮不追求一次问完所有信息，优先补足推荐必需核心字段。
departure_area / activity_goal / time_window 以 text/custom 为主；transport_hint 适合 single_choice + custom。
偏好字段优先用 single_choice / multi_choice，每题允许“其它/补充信息”，返回用户自定义文本，不把 Other 写成业务值。
短输入（如“周末想出去走走”）触发第一轮：departure_area / activity_goal / time_window。
自然语言已含部分核心字段时只问缺失字段。
问题优先级：departure_area → activity_goal → time_window → transport_hint → terrain_tolerance / safety_priority（风险触发）→ scenery / preference / avoid → ability_hint。
```

sufficiency_check 规则（设计理由）：

```text
基础充分条件：activity_goal / departure_area / time_window / transport_hint 全部确认。
能力来源：推荐匹配主要读取用户能力画像；ability_hint 只表达本次主观强度偏好或覆盖项。
风险场景加问：目标 / 标签 / 原话涉及雪、冰雪路、野路、亲子、新手、安全优先时，需确认 terrain_tolerance 或 safety_priority，未确认不进入推荐。
confirmed_context 返回可展示摘要，不返回完整内部 context_state。
```

### ability_hint 边界（设计理由）

```text
用户能力画像是能力匹配的主要来源。
ability_hint 只记录本次对话里的主观强度偏好或覆盖说明，不属于基础核心字段。
用户表达“这次想轻松一点”时可写入 ability_hint，但不能据此改写用户长期能力画像。
```

### agent_runs 状态语义（设计理由）

```text
running：workflow 正在执行。
waiting_user：workflow 产出 ask_user_choice，等待用户选择；本次 AgentRun 已落库并结束。
succeeded：已完成本轮处理，可能返回候选推荐或普通回答。
failed：workflow 失败，接口返回错误并写入可追踪事件。
HTTP 实现中不要求一个 AgentRun 长时间挂起；用户提交 choice-result 后创建新的 AgentRun 基于 context_state 继续推进。从产品视角会话状态未停止（TripPlan 与 context_state 持续存在）。
```

## 暴露的权衡

- 用 trip_plan_messages.content_type + payload 表达 choice_request / choice_result，而非独立 choices 表：本轮查询与审计成本可接受；若后续发现明显过高，再分表。
- choice_request 不设 TTL：利于历史会话异步恢复，代价是 active 判定须严格按消息时间线计算。
- 不支持部分答案提交：前端可逐题呈现，但后端语义简单；代价是用户中途退出需整组重答。
- 场景化 sufficiency（scenario_based）而非固定字段全集：避免无风险场景过度追问，代价是风险触发表需持续维护。
- ability_hint 不作基础核心字段：避免短期偏好误改能力画像，代价是本次强度偏好须单独表达。

> 契约级规则（端点、字段表、错误码、白名单、迁移点）见 API_CONTRACT / DATABASE_DESIGN / TEST_PLAN；本文件只保留设计理由、对齐日志与权衡。
