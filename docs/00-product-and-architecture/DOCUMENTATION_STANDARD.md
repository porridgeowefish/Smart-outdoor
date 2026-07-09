# 文档管理规范

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: this document defines documentation rules for Smart_outdoor.

## 1. 核心原则

Smart_outdoor 使用：

```text
docs-as-code + 文档驱动开发 + 敏捷切片交付
```

文档和代码在同一仓库维护，接口、数据库、Agent workflow、测试策略变化时，文档必须在同一轮任务中同步更新。

## 2. 单一事实源

禁止为同一件事维护多份互相复制的长文档。

允许：

```text
入口文档做索引
总览文档做摘要
详细文档拥有事实源
```

禁止：

```text
在 AGENTS.md、CLAUDE.md、README、迭代文档中重复粘贴同一份长 API 契约
旧文档改名为 _v1 / _v2 后继续并行维护
用聊天记录替代 ADR
```

## 3. 两类文档

### 3.1 需求分析与架构设计

位置：

```text
docs/00-product-and-architecture/
```

内容：

```text
用户洞察
产品场景
领域模型
系统架构
Agent 架构
数据模型
API 契约策略
ADR
```

不包含：

```text
每日进度
临时讨论
某个 slice 的详细测试清单
```

### 3.2 敏捷迭代交付

位置：

```text
docs/01-iterations/iteration-XX-name/
```

每一轮迭代必须包含[每轮必备文档清单](./agent-rules/20-iteration-delivery.md)。迭代文档只描述本轮交付，不重复长期架构全文。

## 4. API 契约规则

最终事实源：

```text
FastAPI route
Pydantic V2 Request / Response model
/openapi.json
前端 OpenAPI 生成类型
```

Markdown API 文档只解释：

```text
接口用途
业务规则
错误码
关键样例
验收重点
```

禁止前端手写后端 Response 类型。

## 5. 数据库文档规则

数据库设计必须说明：

```text
本轮新增/修改表
字段含义
关键约束
权限与归属规则
与已有领域对象的关系
```

全局数据模型放在架构模块；本轮落地细节放在迭代模块。

## 6. ADR 规则

当出现以下情况时必须新增 ADR：

```text
技术栈或基础设施取舍
数据模型边界取舍
Agent workflow 关键策略
Mock / Real 切换策略
安全、隐私、证据约束策略
```

ADR 模板：

```text
# ADR-NNNN Title

Status: proposed | accepted | superseded
Date: YYYY-MM-DD

## Context
## Decision
## Consequences
## Alternatives Considered
```

已接受 ADR 不回改历史结论；新决策新增 ADR 并标记 supersedes。

ADR 触发场景对应的长期文档同步落点见 [agent-rules/10-documentation-governance.md](./agent-rules/10-documentation-governance.md) 的架构变更落点表。

## 7. AI Agent 协作规则

AI coding agent 开工前必须：

```text
1. 读取 docs/INDEX.md
2. 判断任务属于产品架构还是某轮迭代
3. 读取对应目录的 README 和相关事实源
4. 若文档缺失，先补文档草案，再实现
```

AI 不得：

```text
基于 PRD 愿景直接扩大 MVP 范围
忽略当前迭代验收标准
绕过 OpenAPI 类型生成约束
把无证据户外安全结论写成确定事实
```

## 8. 文档状态字段

长期文档建议包含：

```text
Status
Owner
Last reviewed
Source of truth
```

状态建议：

```text
draft
active
deprecated
superseded
```

## 9. 完成定义

一个迭代完成时，文档必须满足：

```text
用户故事清楚
API 契约已实现或明确标记 pending
数据库设计与代码一致
测试计划有对应测试或说明
验收标准可以人工验证
DELIVERY_NOTES 记录实际交付和遗留风险
```

## 10. 迭代文档模板

每轮迭代必须沉淀一组标准文档，包括 `README.md` 与 6 份专项文档，共 7 份。

```text
README.md
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

所有迭代文档必须在文件顶部包含这 4 行 front matter（必须；覆盖 §8 对长期文档的“建议”措辞），格式为纯键值对（无 yaml `---` 围栏），与 §6 ADR 模板一致：

```text
Status
Owner
Last reviewed
Source of truth
```

本章为每类文档规定：用途、标准骨架、硬规则、最小范例。除特殊说明外，模板中的标题应保持稳定，不应随意改名。

### 10.0 推荐填写顺序

建议每轮迭代按以下顺序填写文档：

```text
1. README.md
2. USER_STORIES.md
3. ACCEPTANCE_CRITERIA.md
4. API_CONTRACT.md
5. DATABASE_DESIGN.md
6. TEST_PLAN.md
7. DELIVERY_NOTES.md
```

该顺序对应：

```text
目标与范围
用户价值
黑盒验收
接口契约
数据结构
测试验证
交付记录
```

原则上，应先明确“本轮为什么做、给谁带来什么价值、如何验收”，再进入接口、数据库和测试设计，避免实现倒推需求。

注：以上是填写顺序；§10.1–10.7 的章节编号是目录组织顺序，二者独立。

---

### 10.1 README.md

#### 用途

`README.md` 用于说明本轮迭代的目标、范围、边界和历史来源。它是本轮迭代的入口文档，不承载 API、数据库、测试细节。

#### 标准骨架

```text
## 用户闭环          ← 可选，1-3 句 narrative
## 本轮目标
## 范围
### 本轮覆盖
### 暂不进入
## 历史来源
```

#### 硬规则

````text
本轮目标 / 范围使用 ```text``` 围栏，每行一条。
不使用表格表达本轮目标。
用户闭环 为可选节，用于 1-3 句话说明本轮在产品闭环中的位置，可省略。
不写散文式背景说明。
暂不进入必须显式列出本轮不做的事项。
历史来源使用 markdown 链接，指向 00 长期文档或兄弟迭代文档。
对齐阶段可临时增加 ## 当前阶段 / ## 待对齐问题。
对齐完成后，应删除临时对齐标题。
不在 README.md 复述 API / DB / 测试细节，避免破坏单一事实源。
````

#### 最小范例

````text
## 本轮目标

```text
完成路线收藏能力的最小闭环。
支持用户收藏和取消收藏路线。
为后续推荐系统提供用户兴趣信号。
```

## 范围

### 本轮覆盖

```text
用户收藏路线。
用户取消收藏路线。
用户查看已收藏路线列表。
```

### 暂不进入

```text
不做收藏夹分组。
不做收藏推荐。
不做批量收藏管理。
```

## 历史来源

* [FUTURE_PLANNING.md](../../00-product-and-architecture/FUTURE_PLANNING.md)
* [iteration-08 README](../iteration-08-agent-v2-choice-based-requirement-convergence/README.md)
````

---

### 10.2 USER_STORIES.md

#### 用途

`USER_STORIES.md` 只记录用户故事，表达“谁希望做什么，以获得什么价值”。它不记录实现方案、字段设计、接口设计或验收细节。

#### 标准骨架

```text
## US-NN.x <动词短语标题>

作为<角色>，我希望<行为>，以便<价值>。
```

#### 硬规则

```text
每条用户故事只写一句话。
句式严格使用“作为X，我希望Y，以便Z”。
角色应优先使用终端用户。
只有确实描述系统内部行为时，才使用“作为系统”。
故事句不写实现细节。
故事句不写字段名。
故事句不写根因注释。
不在 USER_STORIES.md 写验收要点。
所有验收内容统一写入 ACCEPTANCE_CRITERIA.md。
ID 格式为 US-NN.x，其中 NN 表示迭代号，x 为本轮内故事顺序号从 1 递增。
```

#### 最小范例

```text
## US-10.1 收藏路线

作为徒步用户，我希望收藏感兴趣的路线，以便后续快速找到并查看。
```

---

### 10.3 API_CONTRACT.md

#### 用途

`API_CONTRACT.md` 用于解释本轮接口契约，包括接口用途、请求、响应和错误码。接口事实源为 Pydantic Schema 与 `/openapi.json`，本文档不替代真实 schema。

#### 复杂度选择

简单新增端点使用“档一”；涉及多个端点或对既有端点做增量变更时，使用“档二”。

#### 档一：简单端点骨架

```text
## METHOD /path

用途：<一句话>

Request:
<json 样例>

Response:
<json 样例>

错误码:
<每行：HTTP code 错误码字符串 触发条件>
```

#### 档二：多个端点或增量变更骨架

```text
## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|

## 请求 / 响应示例

<json 样例，Optional 增量必须标注>

## 错误码

| HTTP | code | 触发 |
|---|---|---|

## 历史来源
```

#### 硬规则

```text
复杂 body 使用字段表，格式为 | 字段 | 类型 | 必填 | 说明 |。
简单 body 可直接使用 JSON 样例。
错误码必须包含 HTTP 状态码和错误码字符串（code）。档一用 ```text``` 每行“HTTP code 触发条件”；档二用三列表 | HTTP | code | 触发 |。
被取代的端点必须使用 > Superseded by iter-NN 或在 ## 历史来源 中说明。
不写设计理由。
不写对齐结论。
不写草案讨论。
不写待对齐问题。
不写时序说明。
```

#### 最小范例

````text
## POST /api/routes/{route_id}/favorite

用途：收藏指定路线。

Request:

```json
{
  "route_id": 123
}
```

Response:

```json
{
  "route_id": 123,
  "favorited": true
}
```

错误码:

```text
401 AUTH_REQUIRED 未登录用户访问。
404 ROUTE_NOT_FOUND 路线不存在。
409 ROUTE_ALREADY_FAVORITED 路线已被收藏。
```
````

---

### 10.4 DATABASE_DESIGN.md

#### 用途

`DATABASE_DESIGN.md` 用于记录本轮涉及的数据表、字段、结构、约束、迁移和同步点。它只描述数据设计，不承载领域哲学或需求论证。

#### 标准骨架

```text
## 表
## <表名或变更字段集>
## 约束
## 迁移与同步点
```

#### 字段表格式

字段必须使用以下表格格式：

```text
| 字段 | 类型 | 结构 / 取值 | 约束 / 来源 | 本轮变化 |
|---|---|---|---|---|
| current_location | object | {raw_text:str, lat:float|null, lng:float|null} | choice | 新增 |
```

#### 硬规则

```text
字段必须使用带类型的字段表。
禁止只列字段名的裸列表。
类型必须具体。
SQL 列用 SQL 类型（int / str / datetime / bool）；JSON / JSONB 字段用 JSON schema 类型（object / array[str] / {raw_text:str, lat:float|null}）；同一字段表内不混用两套。
字段表内的结构化字段在单元格内联结构（如 {raw_text:str, lat:float|null}）；字段表之外若需展示完整 JSON / YAML 子结构，另起围栏块并标注内部类型。
凡涉及 schema 变更，必须列出须同步的读取点。
不写领域哲学。
不写边界论证。
不写对齐结论。
设计理由如需保留，写入 DELIVERY_NOTES 或 ADR。
本轮变化列取值：新增 / 修改 / 复用 / 废弃。
```

#### 最小范例

````text
## 表

```text
新增 route_favorites。
复用 users。
复用 routes。
```

## route_favorites

| 字段         | 类型       | 结构 / 取值 | 约束 / 来源                | 本轮变化 |
| ---------- | -------- | ------- | ---------------------- | ---- |
| id         | int      | 自增 ID   | primary key            | 新增   |
| user_id    | int      | 用户 ID   | foreign key: users.id  | 新增   |
| route_id   | int      | 路线 ID   | foreign key: routes.id | 新增   |
| created_at | datetime | 收藏时间    | server generated       | 新增   |

## 约束

```text
同一用户不能重复收藏同一路线。
删除路线时，应同步处理对应收藏记录。
```

## 迁移与同步点

```text
新增 route_favorites 表。
须同步路线详情页的收藏状态读取逻辑。
须同步用户中心的收藏列表读取逻辑。
```
````

---

### 10.5 TEST_PLAN.md

#### 用途

`TEST_PLAN.md` 用于记录本轮如何验证功能正确性，包括 service/unit、API、权限、前端、失败路径与验证命令。

#### 标准骨架

```text
## Service / Unit
## API
## 权限
## 前端
## 失败路径
## 验证命令
## 备注
## 历史来源
```

空分类可省略，但 `## 验证命令` 必填。

#### 硬规则

```text
分类标题固定使用 Service / Unit、API、权限、前端、失败路径。
失败路径为可选分类；权限 / 不存在 / 冲突类失败用例可集中归 ## 失败路径，也可按接口归 ## API，同一用例不重复。
每条用例写成一行 bullet。
每条用例使用“条件 → 预期”格式。
用例可带 [US-NN.x] 标签追溯用户故事。
验证命令必须使用 fenced 命令块。
长段说明应压缩为 bullet。
无法压缩的背景说明放入 ## 备注。
```

#### 最小范例

````text
## Service / Unit

- [US-10.1] 用户首次收藏存在的路线 → 创建收藏记录并返回成功。
- [US-10.1] 用户重复收藏同一路线 → 返回已收藏错误。

## API

- [US-10.1] 登录用户请求收藏路线 → 返回 favorited=true。
- [US-10.1] 未登录用户请求收藏路线 → 返回 401。

## 验证命令

```powershell
pytest tests/test_route_favorites.py
```
````

---

### 10.6 ACCEPTANCE_CRITERIA.md

#### 用途

`ACCEPTANCE_CRITERIA.md` 用于记录黑盒验收项，即用户或验收人员可以观察到的系统行为。它不描述内部表名、字段名、算法参数或实现细节。

#### 标准骨架

```text
- [US-NN.x] <用户可观察的验收项>
- [US-NN.x] <用户可观察的验收项>
```

#### 硬规则

```text
所有验收项必须是黑盒可观察行为。
不写表名。
不写字段名。
不写算法参数。
不写内部服务名。
每条 bullet 可使用 [US-NN.x] 追溯用户故事。
```

#### 最小范例

```text
- [US-10.1] 用户可以在路线详情页收藏当前路线。
- [US-10.1] 用户收藏成功后，页面能显示已收藏状态。
- [US-10.1] 用户再次进入该路线详情页时，仍能看到已收藏状态。
- [US-10.1] 用户可以取消收藏已收藏路线。
```

---

### 10.7 DELIVERY_NOTES.md

#### 用途

`DELIVERY_NOTES.md` 用于记录本轮实际交付内容、测试运行结果、遗留风险、对齐决策和暴露的权衡。它是交付复盘文档，不是 API、数据库或测试契约的事实源。

#### 标准骨架

```text
## 交付内容
## 测试运行
## 遗留风险
## 对齐与决策
## 暴露的权衡
```

其中 `交付内容`、`测试运行`、`遗留风险` 必填；`对齐与决策`、`暴露的权衡` 可选。

#### 硬规则

```text
交付内容 / 测试运行 / 遗留风险不得留空。
不得使用 Pending. 作为占位。
交付内容记录本轮实际落地的代码、测试、文档或配置。
测试运行必须包含命令和结果。
遗留风险使用 bullet 记录。
对齐与决策使用日期子节。
调查记录可放入对齐与决策，不混入交付内容。
契约级规则必须回填到 API_CONTRACT / DATABASE_DESIGN / TEST_PLAN 或 ADR。
DELIVERY_NOTES.md 只保留指针或摘要。
```

#### 最小范例

````text
## 交付内容

- 新增路线收藏与取消收藏能力。
- 新增路线详情页收藏状态展示。
- 新增收藏相关 API 测试。

## 测试运行

```powershell
pytest tests/test_route_favorites.py
```

```text
12 passed
```

## 遗留风险

* 收藏列表分页暂未实现。
* 删除路线后的收藏清理策略需要在后续迭代确认。

## 对齐与决策

### 2026-06-14

* 本轮只实现单路线收藏，不实现收藏夹分组。
* 收藏推荐能力推迟到后续迭代。

## 暴露的权衡

* 为降低本轮复杂度，收藏行为只作为用户兴趣信号沉淀，不参与推荐排序。
````

---

## 11. 可操作规格与反废话铁律

核心原则：

```text
契约和设计文档只放可操作元素。
判断、理由、权衡、调查记录不写入契约文档。
短期判断写入 DELIVERY_NOTES。
长期决策写入 ADR。
```

### 11.1 各文档允许与禁止内容

| 文档                     | 允许内容                       | 禁止内容                     |
| ---------------------- | -------------------------- | ------------------------ |
| API_CONTRACT.md        | 端点、IO schema、字段表与类型、错误码、样例 | 设计理由、对齐结论、草案、待对齐问题、时序说明  |
| DATABASE_DESIGN.md     | 表、字段表与类型、约束、迁移同步点          | 领域哲学、边界论证、对齐结论           |
| TEST_PLAN.md           | 测试用例 bullet、验证命令、测试路径      | 长段散文说明、需求背景、设计争论         |
| ACCEPTANCE_CRITERIA.md | 黑盒验收 bullet、用户可观察行为        | 表名、字段名、算法参数、内部服务名        |
| DELIVERY_NOTES.md      | 交付内容、测试结果、风险、短期对齐记录        | 替代 API / DB / TEST 的正式契约 |
| ADR                    | 长期设计决策、重大权衡、不可逆架构选择        | 临时进度记录、普通测试结果            |

### 11.2 类型强制

```text
DATABASE_DESIGN.md 的字段表必须包含类型列。
字段类型必须具体。
API_CONTRACT.md 中复杂 body 必须说明字段类型。
结构化字段必须写清内部结构。
```

### 11.3 轻量追溯

```text
USER_STORIES.md 使用 US-NN.x。
TEST_PLAN.md 用例可带 [US-NN.x]。
ACCEPTANCE_CRITERIA.md 验收项可带 [US-NN.x]。
不强制建立完整追溯矩阵，也不强制每条带标签。
鼓励新增文档带上 [US-NN.x]，便于从用例 / 验收回溯到故事。
```

### 11.4 围栏约定

````text
目标、范围、决策、规则类内容使用 ```text```。
JSON 样例使用 ```json```。
YAML 样例使用 ```yaml```。
PowerShell 命令使用 ```powershell```。
普通 shell 命令使用 ```bash```。
````

### 11.5 判断与理由的归属

```text
短期判断、调查记录、迭代内对齐日志写入 DELIVERY_NOTES.md。
长期设计决策、跨迭代生效规则、架构级权衡写入 ADR。
不得把判断、理由、调查过程混入 API_CONTRACT.md、DATABASE_DESIGN.md、TEST_PLAN.md 或 ACCEPTANCE_CRITERIA.md。
```
