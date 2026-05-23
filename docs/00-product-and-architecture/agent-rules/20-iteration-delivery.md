# 20 迭代交付

Status: active
Owner: project maintainer
Last reviewed: 2026-05-22
Source of truth: MVP iteration delivery rules.

## 读取入口

```text
docs/01-iterations/README.md
对应 docs/01-iterations/iteration-* 目录
docs/00-product-and-architecture/MVP_ROADMAP.md
```

## MVP 顺序

```text
Iteration 01 Auth + User
Iteration 02 Route Upload + Parser
Iteration 03 Route List + Detail
Iteration 04 TripPlan + Agent Mock
Iteration 05 Snapshot / 我的规划
Iteration 06 Ability Profile
Iteration 07 Object Storage + Image Assets
Iteration 08 Agent V2 Choice-based Requirement Convergence
```

## 每轮必备文档

```text
README.md
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

## 交付原则

```text
按用户闭环切片开发。
不得先横向铺满架构空壳。
不得仅凭 PRD 扩展 MVP 范围。
当前迭代文档定义当前交付边界。
```

## 对齐优先工作模式

当进入新迭代或需求边界仍在形成时，采用“先对齐、再实现”的节奏：

```text
先一步步对齐业务目标、用户闭环、接口边界、数据边界、测试和验收口径。
对齐过程中持续沉淀当前迭代文档，不把聊天记录当事实源。
文档契约未完整前，不提前进入批量实现。
文档积累完毕并完成冲突检查后，再按文档统一实现。
实现中发现契约缺口时，先回补文档并重新对齐，再继续编码。
```

## HTML 可视化对齐模式

对齐阶段采用“基于 HTML 的可视化判断和决策 + Markdown 文档积累”的交互模式。

每一次需要人类对齐的内容，Agent 必须先生成一个完整 HTML 对齐页面，而不是只在聊天中要求用户口头确认。

HTML 对齐页面要求：

```text
必须是完整可打开的 HTML 文件。
必须支持翻页或分步骤浏览。
必须尽量一次性覆盖当前阶段所有待对齐问题，避免把同一阶段拆成过多轮零散 HTML。
允许信息和问题更密集；一页可以包含多个相关问题。
首页简介必须列出本次 HTML 覆盖的对齐范围、预计需要判断的主题和导出文件路径。
必须包含可交互选择、判断或填写控件。
必须包含 UML、流程图、状态机、时序图、表格或其它结构化表达信息。
必须能导出用户回答。
必须支持用户一键保存导出结果为 Markdown 文件。
必须清楚标注导出的 Markdown 文件路径或建议文件名。
```

对齐流程：

```text
1. Agent 根据当前待对齐主题生成 HTML。
2. 用户在 HTML 中阅读、选择、填写和判断。
3. 用户从 HTML 导出回答 Markdown，并保存到项目中。
4. 用户说“对齐完毕”。
5. Agent 读取导出的回答 Markdown。
6. Agent 对回答进行归纳、去重、冲突检查。
7. Agent 再修改正式迭代 Markdown 文档。
```

边界：

```text
HTML 是对齐和反馈工具，不是最终事实源。
导出的回答 Markdown 是人类反馈输入，不直接替代正式迭代文档。
正式 Markdown 文档仍是共识积累和实现依据。
没有导出回答 Markdown 时，不应把聊天中的临时表达直接写成最终契约。
```
