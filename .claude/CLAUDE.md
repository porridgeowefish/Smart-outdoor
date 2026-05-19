# CLAUDE.md：Smart_outdoor 协作开发规范

## 项目定位

Smart_outdoor 是一个面向户外徒步/线路规划的 Agent 产品。

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

## Claude 开工顺序

开发前先读：

```text
docs/INDEX.md
docs/00-product-and-architecture/DOCUMENTATION_STANDARD.md
AGENTS.md
```

然后根据任务读取对应迭代目录：

```text
docs/01-iterations/iteration-01-auth-user/
docs/01-iterations/iteration-02-route-upload-parser/
docs/01-iterations/iteration-03-route-list-detail/
docs/01-iterations/iteration-04-trip-plan-agent-mock/
docs/01-iterations/iteration-05-snapshot-my-plans/
docs/01-iterations/iteration-06-ability-profile/
```

不得脱离这些文档自行扩展产品范围。

## 事实源优先级

```text
1. 已实现代码、测试、Pydantic Schema、FastAPI OpenAPI 输出
2. docs/01-iterations 中当前迭代文档
3. docs/00-product-and-architecture 中长期架构和 ADR
4. docs/99-archive/backend-docs-legacy 中历史设计文档
5. design_doc 中 PRD、图和演示材料
```

PRD 是产品愿景，不是 MVP 当前实现范围的最高事实源。

## 开发纪律

本项目采用：

```text
切片开发 + 测试驱动开发 + 契约驱动前后端对接 + 文档驱动开发
```

实施顺序：

```text
Iteration 01 Auth + User
Iteration 02 Route Upload + Parser
Iteration 03 Route List + Detail
Iteration 04 TripPlan + Agent Mock
Iteration 05 Snapshot / 我的规划
Iteration 06 Ability Profile
```

每个 slice 必须满足：

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

## TDD 优先

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

## 契约驱动开发

所有 API Request / Response 必须使用 Pydantic V2 模型。

后端必须生成：

```text
/openapi.json
```

前端必须从 OpenAPI 生成 TypeScript 类型和 API Client。

禁止：

```text
前端手写后端 Response 类型
后端返回裸 dict 给业务层扩散
mock 数据字段和真实接口字段不一致
```

## 文档驱动规则

每轮迭代文档必须按以下结构维护：

```text
README.md
USER_STORIES.md
API_CONTRACT.md
DATABASE_DESIGN.md
TEST_PLAN.md
ACCEPTANCE_CRITERIA.md
DELIVERY_NOTES.md
```

文档更新时机：

```text
开工前：补齐本迭代用户故事、API、测试计划。
改接口：同步 Pydantic Schema、OpenAPI、API 文档。
改表结构：同步 ORM model、数据库设计、测试。
做架构取舍：新增 ADR。
交付后：更新 DELIVERY_NOTES。
```

禁止复制长文档制造多份事实源。总览文档只做索引和摘要。

## Mock / Real 单开关切换

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

mock 和 real 必须使用同一套 Pydantic / OpenAPI 类型。

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

## 安全与私有文件

私有密钥文档只允许本地使用：

```text
docs/99-archive/backend-docs-legacy/PRIVATE_SECRETS.local.md
```

不得在回复、提交信息、Issue、PR 或公开文档中展示真实密钥。

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
