# Database Design

Status: draft
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: ORM models, migrations, intent KB YAML after implementation lands.

## 范围

iter09 **不新增数据表**，复用 iter04/08 核心表。变化：context_state 新增/升级字段 + 意图知识库（YAML）+ 本地向量索引。设计决策见 DELIVERY_NOTES。

## 表

沿用（无变更）：`trip_plans`、`trip_plan_messages`、`agent_runs`、`trip_plan_candidate_routes`。`retrieval_trace` 沿用 `trip_plan_messages.payload`（content_type=choice_request）。不建 `tag_knowledge_items` 表。

## context_state 字段（iter09 相关）

| 字段 | 类型 | 结构 / 取值 | 来源 | iter09 变化 |
|---|---|---|---|---|
| `current_location` | object | `{raw_text:str, lat:float\|null, lng:float\|null}` | choice | **新增** |
| `departure_area` | object | `{raw_text:str, lat:float\|null, lng:float\|null}` | choice/text | **升级**（原 str） |
| `ability_hint` | object | `{level:"beginner"\|"normal"\|"strong", raw_text?:str}` | choice | 主观维度写 level |
| `preference_tags` | array[str] | TAG_TAXONOMY 中文值 | choice | 两层流 tag 卡写 |
| `avoid_tags` | array[str] | TAG_TAXONOMY 中文值 | choice | 两层流 tag 卡写 |
| `scenery_preferences` | array[str] | scenery 英文键 | choice | 补全 |
| `supply_requirement` | str | `"need_supply_points"` 等 code | choice | 补全 |
| `terrain_tolerance` | str | `"avoid_icy_road"` 等 code | choice | 补全 |
| `safety_priority` | str | `"high"` 等 code | choice | 补全 |
| `field_sources` | object | `{field: "user_choice"\|"user_explicit_text"\|"ai_extracted"}` | meta | 沿用 |
| `confirmed_fields` / `missing_fields` | array[str] | — | meta | 沿用 |

`CHOICE_WRITABLE_FIELDS`（backend/app/features/trip_plans/context.py）**新增 `current_location`**。字段来源优先级沿用 iter08：`user_choice > user_explicit_text > ai_extracted`。

## departure_area 类型变更 → 须同步的读取点

```text
context_summary         f-string 拼 → 取 .raw_text
display_context_value   dict 默认分支 → 取 .raw_text
confirmed_context       经 display → 同上
update_context_state    原写 str → 改写 {raw_text, lat, lng}
```

## 意图知识库（第二层，本地 YAML）

`TAG_TAXONOMY`（routes/tag_taxonomy.py）为第一层标准标签库，不另造。第二层意图知识库为本地 YAML（进 git），每条结构：

```yaml
- intent: easy_simple                       # str，主键
  phrases: ["简单", "轻松", "不累"]          # list[str]，触发措辞
  dimensions:                                # list
    - key: physical_ease                     # str
      type: subjective                       # subjective | objective
    - key: terrain_easy
      type: objective
      tag_source: ["公路/铺装路", "石板平路", "土路/机耕路"]   # objective 才有：tag 卡 options
      write_field: preference_tags            # 写入的 context_state 字段
  question_tpl: "你说的'{phrase}'更接近哪一种？"   # str，LLM 润色 ≤100 字
```

首批 intent（内容实现时填充）：`easy_simple` / `stimulating_challenge` / `safety_steady` / `snow_play` / `family` / `night_hike` / `scenery_photo`。

## embedding 与向量索引

```text
AgentLLMProvider.embed_texts(texts: list[str]) -> list[list[float]]   # Protocol 新增必需方法
  OpenAILLMProvider：复用 openai client / openai_api_key / openai_base_url；模型 config 默认（实现时定）
  MockLLMProvider：确定性实现（测试 / 离线兜底）
向量库：chroma 或 faiss（实现时二选一），启动时从 YAML + embedding 构建，本地驻留
召回：余弦 top-K；top-1 < 阈值（默认 0.35，config，key 实现时定）或 provider 失败 → 降级（geo 卡不依赖 embedding）
正向 geocode：复用 backend/app/features/agent_tools/transport.py:_geocode_first（高德 /v3/geocode/geo，地名→Coordinate）
```

不引入 pgvector。

## 历史来源

- ../iteration-08-agent-v2-choice-based-requirement-convergence/DATABASE_DESIGN.md（白名单、payload、来源优先级）
- ../iteration-06-ability-profile/README.md（UserAbilityProfile）
- backend/app/features/trip_plans/context.py、routes/tag_taxonomy.py、llm/provider.py、agent_tools/transport.py
