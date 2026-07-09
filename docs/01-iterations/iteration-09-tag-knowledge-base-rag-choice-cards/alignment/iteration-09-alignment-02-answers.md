# Iteration 09 Alignment 02 Answers

Status: human-feedback
Created from: iteration-09-alignment-02-intent-tag-source.html

## Q1 Goal

- decision: clarify_before_write
- notes: (none)

## Q2 Knowledge Layers

- decision: two_layers
- notes: (none)

## Q3 Simple Route Question

- decision: dimension_first
- notes: (none)

## Q4 Write Model

- decision: separate
- notes: (none)

## Q5 LLM Option Scope

- decision: wording_only
- notes: 注意限制LLM提问长度

## Agent Processing Notes

本文件是 human-feedback 输入，不直接替代正式迭代文档；Agent 已归纳、去重、检查冲突后更新正式 Markdown。

- **Q5 限长**：LLM 生成的提问文案 ≤100 字（与 alignment-01 Q1 note 一致），并在 Schema 层卡死，不只靠 prompt。
- **Q4 separate + B3**：指标与标签分开写入；本轮不引入结构化指标字段（distance/elevation），体力类维度落 `ability_hint(level)` + `preference_tags`。
- **Q3 dimension_first + 封顶 4**：选择卡先问"哪种简单/哪种维度"，规则层把召回维度合并到 ≤4 个再出卡。
- **Q1 clarify_before_write + A2/F2**：写标签严格在用户 choice-results 确认之后；RAG 在召回 ≥2 维度且未被 iter08 覆盖时追加维度追问卡。
- 完整决策与 iter09 HITL 流程规格见各正式文档（API_CONTRACT / DATABASE_DESIGN / USER_STORIES / ACCEPTANCE_CRITERIA / TEST_PLAN / DELIVERY_NOTES）。
