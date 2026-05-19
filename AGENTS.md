# AGENTS.md：Smart_outdoor 开发准则

## 项目定位

Smart_outdoor 是面向轻中度户外用户的对话式线路规划 Agent 产品。

核心目标：

```text
通过自然语言理解用户出行需求，结合线路资产、轨迹指标、天气、交通和外部证据，生成可保存、可回看、可分享的户外线路规划。
```

## 开工前必读

人和 AI coding agent 的统一文档入口是：

```text
docs/INDEX.md
```

开发前必须先判断任务属于哪类文档事实源：

```text
需求分析与架构设计：
docs/00-product-and-architecture/

敏捷迭代交付：
docs/01-iterations/iteration-XX-name/
```

文档治理规范：

```text
docs/00-product-and-architecture/DOCUMENTATION_STANDARD.md
```

## 事实源优先级

当文档之间出现冲突时，按以下顺序判断：

```text
1. 已实现代码、测试、Pydantic Schema、FastAPI OpenAPI 输出
2. docs/01-iterations 中当前迭代文档
3. docs/00-product-and-architecture 中长期架构和 ADR
4. docs/99-archive/backend-docs-legacy 中历史设计文档
5. design_doc 中 PRD、图和演示材料
```

PRD 表达产品愿景；MVP 迭代文档表达当前实现边界。不得仅凭 PRD 扩展 MVP 范围。

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
切片开发 + 测试驱动开发 + 契约驱动前后端对接 + 文档驱动开发
```

禁止先横向铺满架构空壳。必须按用户闭环开发。

当前 MVP 迭代顺序：

```text
Iteration 01 Auth + User
Iteration 02 Route Upload + Parser
Iteration 03 Route List + Detail
Iteration 04 TripPlan + Agent Mock
Iteration 05 Snapshot / 我的规划
Iteration 06 Ability Profile
Iteration 07 Object Storage + Image Assets
```

每轮迭代的交付文档在：

```text
docs/01-iterations/
```

每轮迭代至少包含：

```text
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

## TDD 优先

每个 slice 先写测试，再写实现。

最低要求：

```text
API 成功路径测试
API 失败路径测试
权限测试
关键 service 测试
轨迹解析测试
```

不允许先写大量实现，最后再补测试。

## 契约驱动开发

所有 API Request / Response 必须使用 Pydantic V2 模型。

后端必须暴露：

```text
/openapi.json
```

前端必须从 OpenAPI 生成：

```text
TypeScript types
API client 类型约束
mock response 类型约束
```

禁止：

```text
前端手写后端 Response 类型
后端返回裸 dict 给业务层扩散
mock 数据字段和真实接口字段不一致
```

## Mock / Real 可切换

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

## Agent 防幻觉

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

## 关键业务边界

```text
route_asset
线路资产，用于线路库、搜索、规划。

activity_track
用户已完成活动，用于能力画像。
```

二者不能混用。

原始 KML / GPX / GeoJSON 必须保存为文件资产。前端渲染使用解析后的简化 `track_geojson`。

## 文档更新规则

```text
开工前：补齐本迭代 USER_STORIES / API_CONTRACT / TEST_PLAN。
改接口：同步 Pydantic Schema、OpenAPI、迭代 API 文档。
改表结构：同步 ORM model、数据库设计、测试。
做架构取舍：新增 ADR，不把决策藏在聊天记录里。
交付后：更新 DELIVERY_NOTES 和验收状态。
```

禁止维护多份重复事实源。总览文档只做索引和摘要。

## 简洁性

禁止过度设计：

```text
不要为只有一个实现的场景设计抽象层。
不要提前做复杂 repository 框架。
不要迁移旧项目大块代码。
不要把 Agent 写成不可测试的面条逻辑。
不要创建 _v1 / _v2 这类冗余文档。
```

允许的复用：

```text
明确低耦合 utils
明确纯函数
明确 API 调用资料文档
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
文档已同步
```

## 对象存储闭环纪律

涉及 COS / S3 / OSS / MinIO 等对象存储时，不能只用后端 TestClient 或 local provider 测试证明完成。

前端直传对象存储的 slice 必须验证：

```text
ACL 或 bucket policy
CORS 预检和真实浏览器上传
Referer / 防盗链读策略
签名 URL 的读写行为
```

如果上传链路使用 signed PUT URL，交付前必须至少验证一次浏览器等价预检：

```text
OPTIONS signed upload_url
Origin: 部署前端 origin
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: content-type
```

云端验收必须同时覆盖读写两条链路：

```text
POST /api/storage/upload-credentials
前端或浏览器等价方式直传文件
上传完成后的业务 complete 接口
业务详情页可读取对象和渲染结果
空 Referer / 非白名单 Referer 的防盗链行为
```

不得把“API 测试通过 + 云端读取通过”误判为“对象存储上传闭环完成”。

对象存储相关部署还必须验证生产环境配置没有被部署脚本覆盖：

```text
STORAGE_PROVIDER
COS_SECRET_ID / COS_SECRET_KEY / COS_TOKEN
COS_BUCKET / COS_REGION / COS_CDN_BASE_URL
```

前端直传完成后，必须验证“业务 complete 接口”确实写库，并在刷新后通过读取接口返回新 key / URL。不能只看对象已经上传到桶里。
