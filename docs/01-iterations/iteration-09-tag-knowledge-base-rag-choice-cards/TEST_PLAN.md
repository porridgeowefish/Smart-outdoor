# Test Plan

Status: draft
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: tests required before this slice can be called done.

## Service / Unit

- [US-09.1] geo 选择卡值 → 正向 geocode → {raw_text,lat,lng}。
- [US-09.1] geocode 服务缺失时降级（存 raw_text、标记未 geocode），不阻塞。
- [US-09.1] CHOICE_WRITABLE_FIELDS 含 current_location；departure_area 结构化升级后 iter08 读取点不破。
- 意图知识库加载（YAML）与向量索引构建（mock embedding，确定性）。
- [US-09.2] 召回正向意图与维度；维度正确标注 subjective / objective。
- 维度合并到 ≤4：规则层按 dimension_map 归并 + confidence 降序（非 LLM），丢弃项进 retrieval_trace。
- [US-09.3] 两层流：主观维度 → ability_hint{level}，不出 tag 卡；客观维度 → 维度卡 → tag 卡（TAG_TAXONOMY 值）→ 写 preference/avoid/scenery/supply。
- [US-09.3] tag 卡跨轮分批：选中 >3 个客观维度时分多个 choice_request，每轮 ≤3 题。
- [US-09.2] A2/F2：召回 ≥2 维度且未被 iter08 覆盖 → 触发维度卡；已覆盖 → 不追加。
- wording_only：LLM 产物只改 label/description/排序；option.value 不被改动。
- ≤100字：LLM 生成的 question 经 Schema 校验 ≤100 字；超长截断/重试。
- [US-09.4] 补全：scenery_preferences / supply_requirement / terrain_tolerance / safety_priority 经两层流写入。
- 自定义映射：custom_text 映射到最近 TAG_TAXONOMY 标准值；映射不上则保留 custom_text。
- [US-09.5] 降级：embedding provider 抛错/超时，或 top-1 < 阈值 → 回退 iter08 规则式 options；geo 选择卡仍可用；retrieval_trace.degraded=true。

## API

- [US-09.2] POST /api/trip-plans/messages 对含隐含维度的输入返回两层卡（第1轮维度卡；option 带 source；retrieval_trace 在 payload）。
- POST /choice-results 提交维度选择 → 生成第2轮 tag 卡；提交 tag 选择 → 按写入表落 context_state。
- [US-09.1] POST /choice-results 提交 geo 选择 → geocode → current_location / departure_area 结构化。
- 无效 tag value / 非 options 来源的 value 返回明确错误（iter08 校验沿用）。

## 权限

- 用户不能提交他人 TripPlan 的 choice_request（404 CHOICE_REQUEST_NOT_FOUND）。
- 用户不能读取或恢复他人 TripPlan 的 retrieval payload。

## 前端

- 选择卡展示 RAG 辅助 options，逐题呈现（沿用 iter08）；维度卡为 multi_choice，tag 卡依选中维度动态生成。
- 历史恢复时最近一次 active choice_request 仍可交互。
- [US-09.6] 召回说明不展示成事实证据或安全承诺（无置信度展示）。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test_iter9_tmp.db'; pytest tests/trip_plans/test_agent_workflow_units.py tests/trip_plans/test_trip_plan_agent_api.py
$env:DATABASE_URL='sqlite:///./test_iter9_tmp.db'; pytest
```

新增切片预期测试路径（实现时落盘）：

```text
tests/trip_plans/test_intent_kb.py          意图库加载、召回、维度合并、subjective/objective 标注
tests/trip_plans/test_rag_options.py        两层流、tag 卡跨轮分批、wording_only、≤100字、A2/F2
tests/trip_plans/test_geo_extraction.py     geo 选择卡 + geocode + 结构化 + 服务缺失降级
tests/llm/test_provider_embedding.py        embed_texts 真实/mock 切换
```

注：向量索引在测试中用 mock embedding 构建内存索引，不依赖具体 chroma/faiss 实现，避免测试绑死选型。
