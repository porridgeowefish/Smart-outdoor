# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: automated tests after implementation lands.

## API 测试

```text
POST /api/trip-plans/messages 在信息不足时返回 run_status=waiting_user。
waiting_user 响应包含 choice_request，candidate_routes=[]。
choice_request questions 每项包含 type、field、question、header、options、multi_select、allow_custom。
choice_request 一次最多 3 个问题。
POST /api/trip-plans/{trip_plan_id}/choice-results 接收合法 answers 并更新 context_state。
choice-results 提交后如果仍不足，继续返回下一组 choice_request。
choice-results 提交后如果足够，返回 run_status=succeeded 和 candidate_routes。
GET /api/trip-plans/{trip_plan_id}/messages 可以恢复 choice_request 和 choice_result payload。
confirmed_context 返回可展示摘要，不暴露完整内部 context_state。
推荐生成后继续 POST /api/trip-plans/messages 可以追问或修改条件。
closed trip_plan 禁止提交自然语言消息和 choice-results。
```

## 失败路径测试

```text
choice_request_id 不存在返回 CHOICE_REQUEST_NOT_FOUND。
choice_request_id 不属于当前用户返回 CHOICE_REQUEST_NOT_FOUND。
choice_request_id 不属于当前 trip_plan 返回 CHOICE_REQUEST_NOT_FOUND。
field 不在 context_state 白名单返回 INVALID_CHOICE_RESULT。
value 不在 options 且 allow_custom=false 返回 INVALID_CHOICE_RESULT。
multi_select=false 但 value 为数组返回 INVALID_CHOICE_RESULT。
multi_select=true 但 value 不是数组返回 INVALID_CHOICE_RESULT。
空 answers 返回 422 或 INVALID_CHOICE_RESULT。
```

## Service / Workflow 测试

```text
只允许 choice-result 写入 context_state 白名单字段。
choice-result 直接写入 context_state。
choice-result 覆盖同字段的 AI 抽取值。
AI 后续抽取不得静默覆盖 user_choice 字段。
用户自然语言明确修改可以覆盖 user_choice，并把来源标记为 user_explicit_text。
choice-result 覆盖同一 field 的旧值时，confirmed_fields 同步更新。
field_sources 记录 user_choice / user_explicit_text / ai_extracted。
missing_fields 只包含基础核心字段、风险场景阻塞字段或当前 choice_request 需要确认的字段。
冲突输入触发 clarification choice_request，不直接召回路线。
sufficiency_check 在基础核心字段满足后通过；风险场景必须额外确认 terrain_tolerance 或 safety_priority。
ability_hint 不作为默认基础核心字段。
有用户能力画像时，能力匹配主要读取用户能力画像。
用户本轮表达 ability_hint 时，只影响本次偏好或推荐解释，不改写用户能力画像。
推荐后修改关键条件会创建新的 AgentRun 并重新召回。
历史候选保留，但 conversation 默认返回最近一次 AgentRun 的候选。
```

## 前端测试

```text
assistant message 的 choice_request 渲染为选择栏。
同一轮多个问题逐步呈现，使用单题翻页或局部卡片平移。
单选问题只能选一个。
多选问题可以选多个。
allow_custom=true 时可以提交自定义输入。
range 控件本轮不出现。
提交选择后出现用户选择摘要。
选择后如果仍需确认，继续展示下一组选择栏。
选择后如果已满足条件，展示候选线路卡片。
加载历史会话时可以恢复未完成选择栏。
推荐后输入追问时沿用当前 trip_plan。
```

## LLM / Mock 切换测试

```text
mock provider 可稳定产出 choice_request。
real provider 输出经过 Pydantic schema 校验。
real provider 输出非法 choice_request 时降级为可控 waiting_user。
mock / real 切换不改前端页面代码。
```
