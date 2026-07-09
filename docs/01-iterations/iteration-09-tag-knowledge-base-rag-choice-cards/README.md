# Iteration 09 Tag Knowledge Base + RAG-assisted Choice Cards

Status: draft
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this iteration directory after alignment is completed; implementation and tests become authoritative after this slice lands.

## 用户闭环

用户在“出去走走”输入自然语言后，系统借助标签知识库把用户原话中隐含的方向转成可点击、可确认、可修改的选择卡。用户确认后，系统按主观强度（相对能力）和客观需求（标准标签）区分写入，再继续 Iteration 08 的选择式需求收敛流程。

## 本轮目标

```text
把召回所需的字段提全、提准（不修召回——召回精确化是后续迭代）：
  geo 精确化：current_location 新增 + departure_area 升级为 {raw_text,lat,lng}。
  两层 intent→tag：主观维度落 ability_hint；客观维度经维度卡多选 → tag 卡挑 TAG_TAXONOMY。
  补全被召回忽略的字段：scenery_preferences / supply_requirement / terrain_tolerance / safety_priority。
保留 mock / real provider 可切换；避免 RAG 直接下结论或安全断言。
```

## 范围

### 本轮覆盖

```text
geo：current_location / departure_area 选择卡 + 后端正向 geocode → {raw_text,lat,lng}。
意图知识库（本地 YAML）+ 本地向量索引 + 真实 embedding（mock 兜底）。
意图条目带 dimension（subjective / objective）+ dimension_map + question_tpl。
两层 intent→tag：维度卡 multi_choice(≤4) → 客观维度 tag 卡（TAG_TAXONOMY，跨轮分批≤3）→ 写标准字段；主观维度落 ability_hint。
补全 scenery_preferences / supply_requirement / terrain_tolerance / safety_priority。
召回不足 / provider 失败降级为 iter08 规则式选择卡（geo 卡不依赖 embedding）。
```

### 暂不进入

```text
召回排序/过滤修复（含用 geo / scenery / supply 等做距离与偏好过滤）——后续迭代。
group_profile / budget_hint / communication_requirement / emergency_requirement（deferred）。
pgvector / PostGIS / 大规模向量库。
自动替用户判定最终偏好；近期路况、天气、开放状态等外部事实断言。
线路召回重排和能力匹配升级；LangGraph 两阶段规划工作流。
```

## 历史来源

- [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
- [AGENT_ARCHITECTURE.md](../../00-product-and-architecture/AGENT_ARCHITECTURE.md)
- [DOMAIN_MODEL.md](../../00-product-and-architecture/DOMAIN_MODEL.md)
- [iteration-08 README](../iteration-08-agent-v2-choice-based-requirement-convergence/README.md)
