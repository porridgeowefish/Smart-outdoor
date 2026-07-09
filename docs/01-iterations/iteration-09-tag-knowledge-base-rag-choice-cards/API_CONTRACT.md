# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic schemas and OpenAPI after implementation lands.

## 范围

iter09 复用 iter08 双入口与 choice_request / choice_result 契约，**不新增端点、不改核心结构**，仅新增 Optional 字段与可写字段。流程与设计决策见 README、DELIVERY_NOTES。iter08 完整契约见 ../iteration-08-agent-v2-choice-based-requirement-convergence/API_CONTRACT.md。

## 端点

| 方法 | 路径 | iter09 变化 |
|---|---|---|
| POST | `/api/trip-plans/messages` | 响应 `choice_request` 的 options 来源改为 RAG 召回；新增 Optional 字段 |
| POST | `/api/trip-plans/{trip_plan_id}/choice-results` | 新增可写字段 `current_location`；`departure_area` 接受结构化值 |

## choice_request schema 增量（Optional，前端不消费）

iter08 的 question/option 结构不变（type/field/question/header/multi_select/allow_custom/options[].{label,value,description}）。iter09 新增：

```json
// option.source（Optional）
{
  "type": "tag_retrieval",
  "intent": "easy_simple",
  "matched_dimensions": ["physical_ease"],
  "confidence": 0.72
}
// choice_request.retrieval_trace（Optional）
{
  "query_text": "希望线路比较简单",
  "matched_intents": [{"intent": "easy_simple", "dimensions": ["physical_ease","terrain_easy"]}],
  "provider": "openai_embedding",
  "degraded": false
}
```

## question 类型（iter09 产出 3 种）

| question.field | type | options 来源 | option.value |
|---|---|---|---|
| `current_location` / `departure_area` | single_choice + allow_custom | 城市枚举 + custom | 地名字符串 |
| `intent_dimensions`（A2 维度卡） | multi_choice | RAG 召回维度，规则层合并 ≤4 | dimension 键 `dim_*` |
| `preference_tags` / `avoid_tags` / `scenery_preferences` / `supply_requirement` / `terrain_tolerance` / `safety_priority` | single/multi_choice | TAG_TAXONOMY / code 枚举 | 见下 |

## option.value 取值

```text
preference_tags / avoid_tags            → TAG_TAXONOMY 中文值（"公路/铺装路"）
scenery_preferences                     → scenery 英文键（snow_view / forest）
terrain_tolerance / safety_priority / supply_requirement → 英文 code（avoid_icy_road / safety_first / need_supply_points）
intent_dimensions（A2 维度卡）          → dimension 键（dim_physical_ease 等），不直接落库，规则层转写
current_location / departure_area       → 地名字符串，后端 geocode → {raw_text,lat,lng}
label 一律中文。
```

## 请求 / 响应示例

### POST /api/trip-plans/messages 响应（第 1 轮：geo + 维度卡）

```json
{
  "trip_plan_id": "tp_123",
  "run_status": "waiting_user",
  "choice_request": {
    "choice_request_id": "choice_req_123",
    "questions": [
      {
        "type": "single_choice", "field": "current_location",
        "question": "你在哪个城市出发？", "header": "出发地",
        "multi_select": false, "allow_custom": true,
        "options": [
          {"label": "深圳", "value": "深圳"},
          {"label": "成都", "value": "成都"},
          {"label": "北京", "value": "北京"}
        ]
      },
      {
        "type": "multi_choice", "field": "intent_dimensions",
        "question": "你说的\"轻松\"更接近哪几种？", "header": "轻松类型",
        "multi_select": true, "allow_custom": false,
        "options": [
          {"label": "体力轻松", "value": "dim_physical_ease", "source": {"type": "tag_retrieval", "intent": "easy_simple", "matched_dimensions": ["physical_ease"], "confidence": 0.80}},
          {"label": "路面好走", "value": "dim_terrain_easy", "source": {"type": "tag_retrieval", "intent": "easy_simple", "matched_dimensions": ["terrain_easy"], "confidence": 0.74}},
          {"label": "容易导航", "value": "dim_navigation_easy", "source": {"type": "tag_retrieval", "intent": "easy_simple", "matched_dimensions": ["navigation_easy"], "confidence": 0.61}},
          {"label": "更稳妥", "value": "dim_safety_margin", "source": {"type": "tag_retrieval", "intent": "easy_simple", "matched_dimensions": ["safety_margin"], "confidence": 0.58}}
        ]
      }
    ],
    "retrieval_trace": {
      "query_text": "希望线路比较简单",
      "matched_intents": [{"intent": "easy_simple", "dimensions": ["physical_ease","terrain_easy","navigation_easy","safety_margin"]}],
      "provider": "openai_embedding", "degraded": false
    }
  }
}
```

### POST /api/trip-plans/{id}/choice-results 请求（提交第 1 轮）

```json
{
  "choice_request_id": "choice_req_123",
  "answers": [
    {"field": "current_location", "value": "深圳", "label": "深圳", "custom_text": null},
    {"field": "intent_dimensions", "value": ["dim_terrain_easy"], "label": ["路面好走"], "custom_text": null}
  ]
}
```

后端处理：`current_location` → geocode → `{raw_text:"深圳", lat, lng}`；`dim_terrain_easy`（客观）→ 生成第 2 轮 tag 卡；主观维度键（如 `dim_physical_ease`）→ 直接写 `ability_hint`，不出 tag 卡。

### 第 2 轮响应（依第 1 轮选中 `dim_terrain_easy`）

```json
{
  "run_status": "waiting_user",
  "choice_request": {
    "choice_request_id": "choice_req_124",
    "questions": [
      {
        "type": "multi_choice", "field": "preference_tags",
        "question": "路面想要哪种？", "header": "路面",
        "multi_select": true, "allow_custom": true,
        "options": [
          {"label": "公路/铺装路", "value": "公路/铺装路"},
          {"label": "石板平路", "value": "石板平路"},
          {"label": "土路/机耕路", "value": "土路/机耕路"}
        ]
      }
    ]
  }
}
```

提交第 2 轮后，挑中的 TAG 写入 `context_state.preference_tags`（source=user_choice），`run_status` 依 sufficiency_check 转为 succeeded 或下一组问题。

## context_state 写入（iter09 可写字段）

经 choice-results 写入、source=user_choice：`current_location`（新）、`departure_area`（结构化）、`ability_hint`、`preference_tags`、`avoid_tags`、`scenery_preferences`、`supply_requirement`、`terrain_tolerance`、`safety_priority`。完整白名单与字段类型见 DATABASE_DESIGN。

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 409 | CHOICE_REQUEST_NOT_ACTIVE | choice_request 非 active（旧 / 已答 / 被替代） |
| 404 | CHOICE_REQUEST_NOT_FOUND | id 不存在或不属于当前用户 / trip_plan |
| 422 | （iter08 沿用） | value 不在 options、field 非白名单 |
| 200 | geocode 降级 | geocode 失败：存 `raw_text`、`lat/lng=null`，`retrieval_trace.degraded=true`，不阻塞 |

## 硬约束（写入 Schema）

```text
question ≤100 字（Schema maxLength）。
option.value ∈ 知识库/规则层枚举（wording_only）：LLM 只产 label/description/排序/提问文案。
options 2-4 个/题；tag 卡跨轮 ≤3 题/choice_request（沿用 iter08）。
option.source / retrieval_trace 均 Optional，前端不消费（payload_internal）。
current_location / departure_area 须经 geocode 落 {raw_text,lat,lng}。
```

## 历史来源

- ../iteration-08-agent-v2-choice-based-requirement-convergence/API_CONTRACT.md（choice_request / choice_result 完整契约）
- DATABASE_DESIGN.md（context_state 字段、意图 KB、geocode / vector 落地）
