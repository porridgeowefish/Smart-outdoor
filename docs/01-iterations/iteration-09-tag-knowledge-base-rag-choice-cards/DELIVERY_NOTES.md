# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-15
Source of truth: implementation notes after this slice lands.

## 交付内容

- 两轮 HTML 对齐 + 范围定稿 + 6 份正式文档按 DOCUMENTATION_STANDARD §10/§11 收敛（含 9 轮历史文档全量回填）。
- geo 精确化：`context_state.current_location` 新增、`departure_area` 升级为 `{raw_text, lat, lng}`；新增 `backend/app/features/geo/forward.py` 公开正向 geocode（尊重 `use_mock_amap`）；`context.geocode_location` 纯函数（lon→lng 在边界唯一映射）；选择卡经 service `_enrich_geo_fields` geocode 落库，mock 下优雅降级（lat/lng=null）。
- embedding：`AgentLLMProvider.embed_texts` 扩展（OpenAI `embeddings.create` + Mock 稀疏正交确定性向量 + 失败兜底回 mock）；新增 `EMBEDDING_MODEL` 配置。
- 意图知识库 + 两层流：`backend/app/features/trip_plans/intent_kb.py`（6 个 DIMENSIONS：主观 physical_ease / stimulating；客观 terrain / scenery / safety / service / `merge_dimensions` 规则层合并 ≤4）；8 个 INTENTS（含 supply_service），每个 intent 带 `description` 与 phrases 一起 embed（real embedding 语义更稳）；`IntentKB` embedding+substring 双层召回。service 按 `_rag_phase` 出 dimension 卡 → 主观维度落 `ability_hint`（不出 tag 卡）/ 客观维度出 tag 卡（TAG_TAXONOMY，跨轮 ≤3）→ 写 preference_tags / scenery_preferences / avoid_tags / service_preferences；A2/F2（召回 ≥2 维度触发）；geo 卡门控改为 `current_location` unset + 有空位。
- 读者全量同步：`context_summary` / `display_context_value` / `evidence.py`（origin_name、cross_city_hint）走 `geo_raw_text`，兼容结构化 dict 与 legacy str。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test_iter9_tmp.db'; pytest
```

```text
152 passed
```

新增：`tests/geo/test_forward_geocode.py`、`tests/llm/test_provider_embedding.py`、`tests/trip_plans/test_intent_kb.py`、`tests/trip_plans/test_rag_options.py`；并扩充 `test_agent_workflow_units.py` / `test_trip_plan_agent_api.py`（geo + departure_area + 两层流）。

## 遗留风险

- 真实 embedding 启动期依赖 provider 调用（网络 / 成本），测试走 mock；recall 另带 substring 兜底，embedding 失败仍能按关键词召回。
- `_intent_kb_cache` 为进程级单例，按启动时 provider 构建；切换 provider 需重启（或后续加失效机制）。
- 召回忽略字段（scenery / supply / terrain / safety）的“被使用”留给后续召回修复迭代，不在 iter09 验收阻塞。
- 用户在文本里重新提到出发城市时，会经 merge 归一化回 `{raw_text, lat:null}`，丢失之前 choice 路径 geocode 到的坐标（重确认即恢复）。
- navigation 无独立 TAG_TAXONOMY 类目，并入 safety 维度（路标 / 下撤点）；safety_priority / terrain_tolerance 仍走 iter08 风险触发问句（与 tag 卡并行）。

## 对齐与决策

### 2026-06-14 对齐完成 + 文档收敛

范围定为三块：geo 精确化、两层 intent→tag、补全被召回忽略的字段。

```text
geo：current_location 新增 + departure_area 升级为 {raw_text,lat,lng}；选择卡（城市枚举+custom）+ 后端正向 geocode。
两层 intent→tag：
  主观维度（体力/刺激）→ ability_hint{level}，不出 tag 卡，匹配靠画像（profile.level，iter06）+ _metric_tags。
  客观维度（路面/导航/安全/服务/风景）→ 维度卡 multi_choice(≤4) → tag 卡（TAG_TAXONOMY，跨轮分批≤3/轮）→ preference/avoid/scenery/supply。
补全：scenery_preferences / supply_requirement / terrain_tolerance / safety_priority 经两层流提准。
知识源：本地 YAML；向量索引：本地向量库；embedding：扩展 AgentLLMProvider.embed_texts + Mock 兜底；模型 config 默认。
不建表、不引 pgvector；输出标签复用 TAG_TAXONOMY。
```

首批意图知识库条目：easy_simple / stimulating_challenge / safety_steady / snow_play / family / night_hike / scenery_photo；输出标签值一律复用 TAG_TAXONOMY 标准值。

自定义输入复用 iter08 allow_custom + custom_text；尝试映射最近 TAG_TAXONOMY，否则保留 custom_text。管理员维护后台本轮不需要；意图知识库以本地 YAML 维护，进 git。

#### 召回现状诊断（调查记录，iter09 不修）

```text
retrieval.py 实际只读：ability_hint(level) + preference_tags + avoid_tags + 能力画像。
departure_area / current_location / time_window / scenery_preferences / supply_requirement
  / terrain_tolerance / safety_priority / transport_hint / activity_goal —— 提取了全被忽略。
零 geo 过滤 → “在深圳推华山” 的根因（retrieve_visible_routes 查全量 active 线路再排序）。
iter09 不修召回排序/过滤；只把召回所需的字段提全提准，给后续召回修复备料。
```

#### HITL 定位（参照 Claude Code，用法相反）

iter08 已造好完整 HITL 循环。iter09 不造新循环，叠三层提取能力。借鉴 Claude Code 的是机制（幂等 choice_request_id、active 门控、Schema 校验）；不借鉴语义——Claude Code HITL 是授权，iter09 是采集；iter09 把 LLM 降级为文案编辑（wording_only）。

## 暴露的权衡

- 真实 embedding：启动期 provider 调用、网络/成本依赖、测试须保留 mock 路径。
- 本轮不做指标约束：体力类只落 ability_hint，真实指标匹配靠 _metric_tags + 召回排序。
- departure_area 字符串 → 结构化是 schema 变更，须同步 iter08 消费点。
- 正向 geocode：未直接复用 `transport._geocode_first`（它耦合 httpx / transport 证据管线），而是在 `geo/forward.py` 用 urllib（与 reverse 同栈）重写解析；让 transport 复用 `_parse_amap_location` 留后续重构。
- 向量索引：用进程内 `IntentKB`（启动期一次性 embed 全部 phrase），不引 chroma/faiss——意图库规模小（7 intent / ~28 phrase），内存索引足够；recall 额外带 substring 层，离线可测且 embedding 失败可降级。
- 意图知识库用 Python 模块（`intent_kb.py`）而非 YAML——项目无 pyyaml 依赖，Python 常量同等可编辑、零依赖；YAML 化留后续。
- embedding 模型：新增 `EMBEDDING_MODEL` 配置（默认 text-embedding-3-small）；mock 用稀疏正交确定性向量（同文本→cosine 1.0，异文本→≈0）保证离线可测。

> 契约级流程规则（两轮结构、主观不出 tag 卡、A2/F2、wording_only、降级、匹配）见 API_CONTRACT §硬约束 与 TEST_PLAN，不在本文件重复。
