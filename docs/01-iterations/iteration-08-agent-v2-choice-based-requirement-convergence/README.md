# Iteration 08 Agent V2 Choice-based Requirement Convergence

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this iteration directory; implementation and tests authoritative after slice lands.

## 用户闭环

用户在“出去走走”输入自然语言需求后，系统不直接猜测最终偏好，而是把不确定信息转化为可点击、可确认、可修改的选择卡。用户通过选择卡或填空逐步确认交通、风景、路况、安全、补给、时间等条件；系统把确认结果写入结构化 `context_state`。会话状态不停止，用户可以在同一个 TripPlan 中连续做多个选择，直到需求足够清楚后再进入线路召回和推荐。生成推荐后，会话仍保持可追问状态。

## 本轮目标

```text
引入 ask_user_choice 工具调用，把待确认需求表达为结构化选择卡。
新增 choice-results 入口，把用户选择作为最高可信事实写入 context_state。
支持同一 TripPlan 内多次选择、累积状态、条件满足后生成推荐。
推荐生成后仍可追问、解释、修改条件或换一组推荐。
前端展示选择卡、已确认条件和待确认条件。
保留 mock / real LLM 可切换。
```

## 范围

### 本轮覆盖

```text
single_choice / multi_choice 选择卡。
text / custom 补充输入。
已确认条件摘要（confirmed_context）。
待确认条件提示（missing_fields）。
choice_request / choice_result 结构化落库，支持历史会话恢复。
场景化 sufficiency_check（基础核心字段 + 风险场景阻塞字段）。
```

### 暂不进入

```text
range 控件。
部分答案提交（前端逐题呈现，后端整组接收）。
choice_request TTL / 过期语义。
场景化 sufficiency 风险触发表以外的细分规则。
前端选择卡局部翻页 / 平移的视觉细节实现（本轮只定交互模型）。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- [AGENT_ARCHITECTURE.md](../../00-product-and-architecture/AGENT_ARCHITECTURE.md)
- [iteration-04-trip-plan-agent-mock](../iteration-04-trip-plan-agent-mock/README.md)
- [iteration-06-ability-profile](../iteration-06-ability-profile/README.md)
- [iteration-07-object-storage-image-assets](../iteration-07-object-storage-image-assets/README.md)
- Claude Code / Claude Agent SDK `AskUserQuestion` user input pattern: https://code.claude.com/docs/en/agent-sdk/user-input
