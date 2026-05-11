# 未来规划草案

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-11
Source of truth: discussion notes for future iterations; not an implementation contract.

本文档用于沉淀跨对话形成的产品和架构想法。它不是当前迭代契约，不直接扩大 MVP 范围。进入开发前，必须把对应内容拆进 `docs/01-iterations/iteration-XX-name/`，并补齐用户故事、API、数据库、测试和验收文档。

## 使用原则

```text
记录未来方向，不替代迭代文档。
记录业务问题、解决价值和大致实现方式。
只保留已经讨论过且对路线有影响的想法。
当想法进入开发，迁移到具体 iteration 文档，并在本文标记状态。
```

## 候选迭代顺序

当前已完成或已建立文档的 MVP 迭代到：

```text
Iteration 01 Auth + User
Iteration 02 Route Upload + Parser
Iteration 03 Route List + Detail
Iteration 04 TripPlan + Agent Workflow
Iteration 05 Snapshot / 我的规划
Iteration 06 Ability Profile
```

后续候选顺序建议：

```text
Iteration 07 Object Storage + Image Assets
Iteration 08 Agent V2 Choice-based Requirement Convergence
Iteration 09 Tag Knowledge Base + RAG-assisted Choice Cards
Iteration 10 Route Retrieval Rerank + Ability Match
Iteration 11 Two-stage Planning Workflow + LangGraph
Iteration 12 Evidence Detail Card + SSE Progress
```

## Iteration 07：对象存储与图片资产处理

### 要解决的问题

当前头像、路线封面、轨迹原始文件等资产主要存储在本地路径下。这个方案适合本地开发，但不适合云部署和扩展：

```text
本地路径无法稳定暴露给前端。
多实例部署时文件不共享。
图片原图可能过大，手机端加载和渲染成本高。
头像、封面、轨迹文件缺少统一资产边界。
```

### 业务变化

用户上传头像、路线封面和轨迹文件后，系统通过统一文件资产服务保存。前端拿到可访问 URL，不关心文件在本地、对象存储还是 CDN 后面。

图片类资产需要生成适合手机端展示的压缩版本。轨迹文件是重要数据资产，原始 GPX/KML/GeoJSON 暂不做压缩，只保证完整保存和可追溯。

### 大致实现

```text
引入 StorageService 抽象：
- local provider 用于本地开发
- object storage provider 用于云部署

文件元数据记录：
- storage_provider
- storage_key
- content_type
- size_bytes
- original_filename
- public_url 或可生成 URL 的信息

图片处理：
- 头像生成 thumbnail / display 版本
- 路线封面生成 thumbnail / large 版本
- 前端默认使用压缩版本
- 原图保留，用于后续重新生成或高清场景
```

初始压缩建议：

```text
头像：最大边 512px，目标体积 < 200KB
路线封面：最大边 1280px，目标体积 < 500KB
小卡片缩略图：最大边 480px，目标体积 < 120KB
优先 WebP，必要时回退 JPEG
```

云函数可以作为后续增强：

```text
对象上传后触发云函数
云函数生成图片变体
写回资产元数据或通过回调通知后端
```

## Iteration 08：Agent V2 选择式需求收敛

### 要解决的问题

当前 Agent 可以对话和生成候选，但用户看不到系统到底理解了什么。LLM 抽取不一定稳定，奇怪输入、口语化表达和省略信息容易导致推荐偏差。

更核心的问题是：很多时候用户自己也没有把需求一次性想清楚。户外规划包含交通、强度、风景、路况、安全、补给、通信、时间等多维约束，依赖自由多轮对话会让收敛过程变慢，也不容易测试。

### 业务变化

产品形态从“聊天机器人猜用户意图”转为“任务收敛式 Agent UI”。自然语言仍然是入口，但 Agent 的主要职责是把不确定性转化为可点击、可确认、可修改的选择卡。

用户发送自然语言后，系统先做粗理解，再返回结构化选择卡，例如：

```text
这次更像哪种出行？
- 城市周边轻徒步
- 山野风景路线
- 亲子/朋友休闲路线

交通更倾向？
- 自驾
- 公共交通
- 都可以，帮我权衡

冰雪路况接受程度？
- 尽量不要冰雪路，只看远处雪景
- 可以接受少量冰雪路
- 可以接受明显冰雪路，但需要成熟路线
```

用户通过点击选择卡逐步收敛需求；如果不满意，也可以继续输入自然语言补充。Agent 每次基于用户选择和补充信息更新 `context_state`，达到推荐条件后再进入线路召回。

### 大致实现

```text
收紧 LLM 输出 schema，用 Pydantic 校验粗理解结果。
新增 clarification_cards 结构，支持 single_choice / multi_choice / range / text。
每张选择卡绑定 context_state 字段，例如 transport_preference、intensity、terrain_tolerance。
用户点击选项后，后端把选择写入结构化 context_state。
用户可以继续输入自然语言，Agent 重新生成或补充选择卡。
前端展示选择卡、已确认条件和待确认条件。
保留 mock / real LLM 可切换，并为奇怪输入、短输入、冲突输入编写测试。
```

选择卡响应示例：

```json
{
  "type": "single_choice",
  "field": "transport_preference",
  "title": "这次交通更倾向哪种？",
  "options": [
    { "label": "自驾", "value": "self_drive" },
    { "label": "公共交通", "value": "public_transport" },
    { "label": "都可以，帮我权衡", "value": "flexible" }
  ]
}
```

## Iteration 09：标签知识库与 RAG 辅助选择卡

### 要解决的问题

仅靠人工 synonyms 难以覆盖自然表达。例如“想去玩雪，希望路好走一些”同时包含风景偏好、地形偏好和风险规避。硬编码关键词会越来越脆。

但 RAG 也不应该直接替用户做最终偏好决定。更稳定的方式是：RAG 负责找到“可能相关的方向”，选择卡负责让用户做小方向确认。

### 业务变化

建立标签知识库，用 RAG 从用户原话中召回可能相关的标签、风险和场景维度。系统基于这些召回结果生成选择卡，让用户确认后再沉淀为标准 `preference_tags` 和 `avoid_tags`。

RAG 的角色是辅助收敛，不是自动替用户下结论。

### 大致实现

标签知识库记录：

```text
tag
category
description
positive_phrases
negative_phrases
```

示例：

```text
公路/铺装路：
适合路好走、新手、亲子、轻松徒步等需求。

野路（无明显路径）：
适合探险、野线、挑战；不适合路好走、不想迷路、带小朋友等需求。
```

RAG 流程：

```text
用户原话 + LLM 粗抽取结果
↓
embedding / 语义召回标签知识库中的相关标签和风险维度
↓
生成选择卡 options
↓
用户点击选择
↓
写入标准 preference_tags / avoid_tags / context_state
↓
达到条件后进入线路召回评分
```

示例：

```text
用户输入：
想去玩雪，但不要太危险

RAG 召回方向：
雪山、冰雪路、有路标、下撤点、景区运营管理、野路、无信号

生成选择卡：
你更想要哪种雪景体验？
- 景区/成熟路线，看雪为主
- 山野雪线，有一定挑战
- 只要有雪景，安全优先

冰雪路况接受程度？
- 尽量不要冰雪路，只看远处雪山
- 可以接受少量冰雪路
- 可以接受明显冰雪路，但需要成熟路线
```

MVP 可以先使用内存知识库和 OpenAI embedding；后续规模变大再考虑 pgvector。

## Iteration 10：线路召回重排与用户能力融合

### 要解决的问题

推荐不能只看标签，还必须结合用户能力画像和线路客观指标。比如同样是“挑战”，对于不同能力用户应该对应不同距离、爬升、坡度和移动时间区间。

### 业务变化

系统召回 top3 候选时，需要给出可解释的匹配依据：

```text
哪些偏好标签命中
哪些避开标签触发扣分
距离 / 爬升 / 坡度是否适配
用户能力画像是否支持
为什么推荐这条而不是另一条
```

### 大致实现

召回评分拆成可解释部分：

```text
preference_score
avoid_penalty
ability_score
metrics_score
diversity_score
evidence_score
```

后端返回候选时附带 score breakdown，前端可以展示简短理由。

## Iteration 11：二阶段规划工作流与 LangGraph

### 要解决的问题

如果一次性对 top3 全部调用天气、交通、搜索和 LLM 生成详细卡片，响应慢、成本高，也容易让用户等待时没有反馈。

### 业务变化

规划流程改为两阶段：

```text
第一阶段：
理解需求 -> 标签方向召回 -> 选择卡收敛需求 -> 召回 top3 简卡 -> 用户选择线路

第二阶段：
用户选中某条线路 -> 查询天气/交通/搜索证据 -> LLM 生成详细规划卡片 -> 保存
```

### 大致实现

使用 LangGraph 管理 Agent workflow：

```text
extract_context
→ normalize_tags
→ generate_choice_cards
→ wait_requirement_selection
→ retrieve_top_routes
→ wait_route_selection
→ gather_evidence
→ generate_detail_card
→ save_snapshot
```

LangGraph 的价值在于：

```text
显式状态机
可暂停等待用户选择
可恢复上下文
节点可独立测试
比自由 Agent 更容易约束成本和边界
```

## Iteration 12：真实证据详情卡与 SSE 进度反馈

### 要解决的问题

用户在规划时不能干等。天气、交通、搜索、LLM 生成都可能耗时，需要把 Agent 当前阶段反馈给前端。同时详情卡必须标明证据来源，避免户外安全幻觉。

### 业务变化

前端展示阶段进度：

```text
正在理解需求
正在匹配线路
正在查询天气
正在查询交通
正在检索外部证据
正在生成规划
已完成
```

详情卡包含：

```text
推荐理由
能力匹配说明
天气摘要
交通建议
外部证据 URL
风险提示
证据不足说明
```

### 大致实现

```text
前端接入 agent run SSE。
后端在 workflow 各节点写入阶段事件。
候选详情只基于数据库、API 和带 URL 的搜索证据生成。
evaluator 检查绝对安全话术和无证据断言。
```

## 待定问题

```text
对象存储优先选型：S3/MinIO、腾讯云 COS、阿里 OSS 还是部署环境默认服务。
图片压缩优先放在后端同步处理，还是直接设计为云函数异步处理。
RAG 初期是否引入真实 embedding，还是先用可测试的 mock embedding + 规则混合。
选择卡优先支持哪些控件：单选、多选、范围、文本补充是否第一轮全部实现。
LangGraph 是否在 Iteration 11 一次性替换现有 workflow，还是先包裹现有节点逐步迁移。
```
