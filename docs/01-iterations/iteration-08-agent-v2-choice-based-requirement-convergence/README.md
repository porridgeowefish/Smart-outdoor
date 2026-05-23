# Iteration 08 Agent V2 Choice-based Requirement Convergence

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: this iteration directory after alignment is completed; implementation and tests become authoritative after this slice lands.

## 当前阶段

本轮处于对齐与文档积累阶段，暂不进入批量实现。

工作节奏：

```text
先一步步对齐业务目标、用户闭环、接口边界、数据边界、测试和验收口径。
对齐过程中持续沉淀本目录文档。
文档契约完整后，再统一实现。
```

## 用户闭环草案

用户在“出去走走”输入自然语言需求后，系统不直接猜测最终偏好，而是把不确定信息转化为可点击、可确认、可修改的选择卡。

用户通过选择卡或填空逐步确认交通、风景、路况、安全、补给、时间等条件；系统把确认结果写入结构化 `context_state`。会话状态不停止，用户可以在同一个 trip_plan 中连续做多个选择，直到需求足够清楚后再进入线路召回和推荐。

能力强弱优先来自用户能力画像；用户在本轮对话里表达的强度偏好只作为偏好或覆盖项，不作为默认阻塞推荐的基础核心字段。

生成推荐后，会话仍然保持可追问状态。用户可以继续追问、修改条件、要求解释或要求换一组推荐；系统基于同一个 `context_state` 和历史消息继续工作。

## 上下文可信度原则

选择题不是旁路信息，而是对 `context_state` 的高可信写入。它的目的就是替代不稳定的 AI 倾向判断。

写入优先级：

```text
1. 用户在选择题中的显式选择或自定义输入。
2. 用户自然语言中的显式修改，例如“不要自驾了，改公共交通”。
3. AI 从自然语言中抽取出的低置信度倾向。
```

当同一字段已经由用户选择确认后，AI 后续抽取不能静默覆盖；只有用户再次明确选择或明确用自然语言修改时才能覆盖。

## 交互模型草案

本轮借鉴 Claude Code / Claude Agent SDK 的 `AskUserQuestion` 模式：Agent 在执行中需要用户补充信息时，通过工具调用产出结构化问题；宿主 UI 展示选择栏；用户选择或输入自定义内容后，工具调用返回答案，Agent 基于答案继续执行。

项目内不直接绑定 Claude Code SDK，而是抽象为领域工具：

```text
ask_user_choice
```

设计原则：

```text
ask_user_choice 是 Agent workflow 中的交互暂停点，不是最终回复。
工具输入是一个或多个 clarification question。
一个工具调用最多包含 3 个问题，但前端应逐步呈现，使用单题翻页或局部卡片平移，不一次性把所有问题铺满。
问题可以是单选、多选或填空；选项型问题提供 2-4 个推荐选项，并允许自定义补充。
工具返回用户真实选择值；如果用户选择自定义，返回自定义文本，不返回 “Other”。
返回后同一个 AgentRun / TripPlan 继续推进，更新 context_state。
多次 ask_user_choice 可以发生在同一个会话中。
```

## 本轮目标草案

```text
收紧 Agent V2 的需求理解输出 schema。
新增 ask_user_choice 工具调用和 clarification_cards 展示结构，用于表达待确认问题。
支持用户点击选择卡或填写文本后更新 trip_plan.context_state。
支持同一会话内多次选择并累积状态。
推荐生成后支持继续追问和修改条件。
前端展示选择卡、已确认条件和待确认条件。
保留 mock / real LLM 可切换。
为短输入、口语化输入、冲突输入和选择卡提交补测试。
```

## 初始范围草案

本轮优先覆盖：

```text
single_choice 选择卡
multi_choice 选择卡
text 补充输入
已确认条件摘要
待确认条件提示
```

待进一步对齐：

```text
场景化 sufficiency 规则的具体触发条件表。
前端选择卡局部翻页/平移的具体视觉细节。
```

已对齐：

```text
自然语言继续使用 POST /api/trip-plans/messages。
选择结果使用 POST /api/trip-plans/{trip_plan_id}/choice-results。
选择结果直接写入 trip_plans.context_state，是最高可信的用户确认事实。
等待用户选择时，本次 AgentRun 落库为 waiting_user。
用户提交选择后创建新的 AgentRun，基于同一个 TripPlan 继续推进。
choice_request 和 choice_result 通过 trip_plan_messages.content_type + payload 恢复。
context_state 字段分为基础核心字段、场景化阻塞字段、偏好字段和元字段。
基础核心字段不包含 ability_hint；能力匹配主要读取用户能力画像。
基础核心字段里，departure_area / activity_goal / time_window 以填空为主，transport_hint 适合选择题。
偏好字段以选择题 + 其它/补充信息为主。
场景化充分条件采用 scenario_based：基础字段满足后，若涉及雪、野路、亲子等风险场景，还必须确认 terrain_tolerance 或 safety_priority。
一轮 ask_user_choice 最多 3 个问题，但前端逐步呈现，不一次性全部展开。
本轮不支持 range 控件。
choice_request_id 使用独立 UUID。
confirmed_context 返回可展示摘要，不返回完整内部 context_state。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- [AGENT_ARCHITECTURE.md](../../00-product-and-architecture/AGENT_ARCHITECTURE.md)
- [iteration-04-trip-plan-agent-mock](../iteration-04-trip-plan-agent-mock/README.md)
- [iteration-06-ability-profile](../iteration-06-ability-profile/README.md)
- [iteration-07-object-storage-image-assets](../iteration-07-object-storage-image-assets/README.md)
- Claude Code / Claude Agent SDK `AskUserQuestion` user input pattern: https://code.claude.com/docs/en/agent-sdk/user-input

## 本轮必补文档

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```
