# Iteration 09 Alignment 01 Answers

Status: human-feedback
Created from: iteration-09-alignment-01.html
Suggested target: docs/01-iterations/iteration-09-tag-knowledge-base-rag-choice-cards/alignment/iteration-09-alignment-01-answers.md

## Q1 Core Goal

- goal_fit: yes
- notes: 对的，直接推荐是LLM做的？注意控制长度，100字以下，比如说

## Q2 Out Of Scope

- out_of_scope: pgvector, rerank, langgraph, external_facts
- notes: 没有问题

## Q3 Knowledge Store

- knowledge_store: local_file
- notes: 我没有明白，我想用的是真实的可以切片检索的知识库，我不知道标签RAG是怎么做的？

## Q4 Retrieval Strategy

- retrieval_strategy: real_embedding
- notes: 对，一样

## Q5 Metadata Exposure

- metadata_exposure: payload_internal
- notes: 我没看懂，RAG召回的是困惑点，还是要深入到具体标签去提问，这个不应该是LLM来做吗？但是如果有多种标签，那么难道就给用户很多选项吗？这样似乎也不对。

## Q6 Acceptance

- done_criteria: unit_tests, api_tests, frontend_minimal, openapi_types
- notes: (none)

## Agent Processing Notes

本文件是 human-feedback 输入，不直接替代正式迭代文档；Agent 已归纳、去重、检查冲突后更新正式 Markdown。

用户在 Q3、Q5 表达的两处困惑已在后续对齐与流程打磨中澄清：

- **Q3「真实可切片检索的知识库」**：`knowledge_store: local_file` 指知识源以本地 YAML 维护（人可编辑、进 git），不等于"不做检索"。检索由真实 embedding + 本地向量库实现（见下）。
- **Q5「召回的是困惑点还是具体标签 / 会不会选项太多」**：tag-RAG 召回的是「意图维度 + 候选标准标签 + 追问模板」。选择卡按维度优先（dimension_first）组织，规则层把候选维度合并到 ≤4 个，不会把几十个标签堆给用户。

2026-06-14 架构确认（结合 alignment-02 与流程打磨）：

```text
知识源：本地 YAML（单一事实源，进 git）。
向量索引：本地向量库（chroma / faiss，实现切片时二选一），启动时从 YAML + embedding 构建。
embedding：扩展现有 AgentLLMProvider.embed_texts()，复用同一 OpenAI 客户端/key/base_url；
          模型走 config 默认，实现时选定；MockLLMProvider 作为测试/离线兜底。
不建表、不引入 pgvector（out_of_scope）。
输出标签值复用现有 TAG_TAXONOMY（backend/app/features/routes/tag_taxonomy.py）。
retrieval_trace 只进 choice_request payload 与日志（payload_internal），前端不展示置信度。
```

硬约束：**LLM 生成的提问文案 ≤100 字**（与 alignment-02 Q5 一致）。

流程打磨结论（详见各正式文档）：

```text
A2 选项源 + 歧义追问：RAG 既给 iter08 已有问题的 options 提供维度候选，
   又在召回 ≥2 维度且未被 iter08 覆盖时（F2）追加维度优先追问卡。
B3 本轮不引入指标约束字段：体力类维度落 ability_hint + preference_tags，
   真实指标匹配靠线路侧 _metric_tags + 召回排序。
封顶 4 个选项；clarify_before_write；wording_only（option.value 必须来自知识库/规则层）。
```
