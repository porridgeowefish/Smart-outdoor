# CLAUDE.md：Smart_outdoor 协作开发规范

## 项目定位

Smart_outdoor 是一个面向户外徒步/路线规划的 Agent 产品。

核心目标：

```text
通过对话式 Agent 理解用户出行需求，结合线路资产、轨迹指标、天气、交通和外部证据，推荐真正可用的户外线路规划。
```

当前 MVP 主入口：

```text
出去走走
我的规划
线路
个人中心
```

## Claude 工作原则

### 1. 先读设计文档，再编码

编码前必须优先阅读：

```text
backend/docs/US-01_API_CONTRACT.md
backend/docs/US-01_DATABASE_DESIGN.md
backend/docs/US-01_AGENT_WORKFLOW.md
backend/docs/US-02_PROFILE_AND_ABILITY_DESIGN.md
backend/docs/US-03_ROUTE_MODULE_DESIGN.md
backend/docs/MVP_IMPLEMENTATION_SLICES.md
```

不得脱离这些文档自行扩展产品范围。

### 2. 切片开发

必须按用户闭环开发，不按技术层横向铺架构。

实施顺序：

```text
Slice 1 Auth + User
Slice 2 Route Upload + Parser
Slice 3 Route List + Detail
Slice 4 TripPlan + Agent Mock
Slice 5 Snapshot / 我的规划
Slice 6 Ability Profile
```

每个 slice 必须满足：

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
没有无用抽象
```

### 3. TDD 优先

每个 slice 先写测试，再写实现。

最低测试要求：

```text
API 成功路径
API 失败路径
权限校验
关键 service 逻辑
轨迹解析逻辑
```

不允许先写大量实现，最后再补测试。

### 4. 契约驱动开发

所有 API Request / Response 必须使用 Pydantic V2 模型。

后端必须生成：

```text
/openapi.json
```

前端必须从 OpenAPI 生成 TypeScript 类型。

禁止：

```text
前端手写后端 Response 类型
后端返回裸 dict 给业务层扩散
mock 数据字段和真实接口字段不一致
```

### 5. Mock / Real 单开关切换

前端页面代码不得关心当前是 mock 还是真实后端。

推荐前端开关：

```text
VITE_USE_MOCK_API=true
```

后端外部依赖开关：

```text
USE_MOCK_LLM=true
USE_MOCK_WEATHER=true
USE_MOCK_AMAP=true
USE_MOCK_SEARCH=true
```

要求：

```text
mock 和 real 使用同一套 Pydantic / OpenAPI 类型。
切换 mock/real 只能改环境变量，不能改页面逻辑。
```

## 技术栈

```text
后端：FastAPI + Python 3.10+
前端：React 18 + TypeScript + Vite + Tailwind CSS
数据库：MVP 可用 SQLite/PostgreSQL，后续可迁移 PostgreSQL
部署：Docker + Docker Compose
```

## 关键业务边界

### route_asset 与 activity_track 不得混用

```text
route_asset
线路资产：用于线路库、搜索、规划、Agent 推荐。

activity_track
用户已完成活动：用于能力画像。
```

用户上传想规划的线路，不等于用户已经完成过这条线路。

### 原始轨迹与渲染轨迹分离

```text
route_files
保存原始 KML / GPX / GeoJSON。

route_analysis_snapshots.track_geojson
保存简化 GeoJSON，用于前端地图渲染。

route_analysis_snapshots 指标字段
保存距离、爬升、海拔、坡度等，用于筛选和推荐。
```

前端地图优先使用 `track_geojson`，不要直接解析原始 KML/GPX。

### manual_tags 是补充语义，不是事实证据

`manual_tags` 用于：

```text
线路展示
线路筛选
Agent 偏好召回
优势标签生成
```

但不能替代：

```text
轨迹指标
天气 API
交通 API
外部证据
```

## Agent 防幻觉要求

Agent 只能基于以下信息输出：

```text
数据库已有信息
API 明确返回的信息
Web 搜索明确返回且带 URL 的信息
```

无证据内容必须降级表达为：

```text
未确认
证据不足
建议出发前核实
```

禁止输出：

```text
放心去
一定适合
路况很好
最近很多人走过
绝对安全
```

除非证据明确支持，且仍应保守表达。

Agent Workflow 固定为：

```text
intent_detection
→ context_update
→ sufficiency_check
→ route_retrieval
→ evidence_search
→ plan_evaluation
→ evaluator
→ response_generation
```

不得把 Agent 写成不可测试的单体函数。

## 简洁性约束

禁止过度设计：

```text
不要为只有一个实现的场景设计抽象层。
不要提前铺复杂 repository 框架。
不要迁移旧项目大块代码。
不要创建无用目录和空文件。
不要创建 _v1 / _v2 这类冗余文档。
```

允许复用：

```text
明确低耦合 utils
明确纯函数
明确 API 调用资料文档
```

## 安全与私有文件

私有密钥文档只允许本地使用：

```text
backend/docs/PRIVATE_SECRETS.local.md
```

不得在回复、提交信息、Issue、PR 或公开文档中展示真实密钥。

正式建仓后必须加入 `.gitignore`。

## 完成反馈格式

每次完成任务后必须说明：

```text
改了哪些文件
完成了哪个 slice 或哪个接口
运行了哪些测试
哪些外部依赖仍是 mock
是否有未完成风险
```

如果没有运行测试，必须明确说明原因。
