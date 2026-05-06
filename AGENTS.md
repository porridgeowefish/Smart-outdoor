# AGENTS.md：Smart_outdoor 开发准则

## 技术栈

```text
后端：FastAPI + Python 3.10+
前端：React 18 + TypeScript + Vite + Tailwind CSS
数据库：MVP 可用 SQLite/PostgreSQL，后续可迁移 PostgreSQL
部署：Docker + Docker Compose
```

## 核心开发纪律

本项目采用：

```text
切片开发 + 测试驱动开发 + 契约驱动前后端对接
```

### 1. 切片开发

禁止先横向铺满架构空壳。必须按用户闭环开发：

```text
注册登录
上传线路
查看线路
对话推荐
保存规划
能力画像
```

每个 slice 必须能独立验收。

### 2. TDD 优先

每个 slice 先写测试，再写实现。

最低要求：

```text
API 成功路径测试
API 失败路径测试
权限测试
关键 service 测试
轨迹解析测试
```

### 3. 契约式编程

所有 API Request / Response 必须使用 Pydantic V2 模型。
禁止在业务层传递裸 dict。

前端禁止手写后端 Response 类型，必须从 OpenAPI 生成。

### 4. API 契约优先

后端 FastAPI 必须暴露：

```text
/openapi.json
```

前端通过 OpenAPI 生成：

```text
TypeScript types
API client 类型约束
mock response 类型约束
```

### 5. Mock / Real 可切换

外部依赖必须可以 mock：

```text
LLM
QWeather
AMap
Tavily
```

推荐后端环境变量：

```text
USE_MOCK_LLM=true
USE_MOCK_WEATHER=true
USE_MOCK_AMAP=true
USE_MOCK_SEARCH=true
```

推荐前端环境变量：

```text
VITE_USE_MOCK_API=true
```

切换 mock/real 时，不允许改页面代码。

### 6. 防幻觉

Agent 只能基于：

```text
数据库已有信息
API 明确返回的信息
Web 搜索明确返回且带 URL 的信息
```

无证据内容只能表达为：

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

### 7. 轨迹数据边界

```text
route_asset
线路资产，用于线路库、搜索、规划。

activity_track
用户已完成活动，用于能力画像。
```

二者不能混用。

原始 KML / GPX / GeoJSON 必须保存为文件资产。
前端渲染使用解析后的简化 `track_geojson`。

### 8. 简洁性

禁止过度设计：

```text
不要为只有一个实现的场景设计抽象层。
不要提前做复杂 repository 框架。
不要迁移旧项目大块代码。
不要把 Agent 写成不可测试的面条逻辑。
```

允许的复用：

```text
明确低耦合 utils
明确纯函数
明确 API 调用资料文档
```

## MVP 实施顺序

```text
Slice 1 Auth + User
Slice 2 Route Upload + Parser
Slice 3 Route List + Detail
Slice 4 TripPlan + Agent Mock
Slice 5 Snapshot / 我的规划
Slice 6 Ability Profile
```

## 每个 slice 的完成定义

```text
测试通过
API 可调用
数据库有数据
前端能看到最小结果
契约类型已生成
mock/real 切换不改页面代码
没有无用抽象
```

## 文档来源

核心设计文档在：

```text
backend/docs/US-01_API_CONTRACT.md
backend/docs/US-01_DATABASE_DESIGN.md
backend/docs/US-01_AGENT_WORKFLOW.md
backend/docs/US-02_PROFILE_AND_ABILITY_DESIGN.md
backend/docs/US-03_ROUTE_MODULE_DESIGN.md
backend/docs/MVP_IMPLEMENTATION_SLICES.md
```
