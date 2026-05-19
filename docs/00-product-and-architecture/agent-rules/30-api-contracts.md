# 30 API 契约与 Mock / Real

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: API contract and mock/real switching rules.

## 读取入口

```text
backend 代码
Pydantic Schema
FastAPI /openapi.json
docs/00-product-and-architecture/API_CONTRACT_STRATEGY.md
当前迭代 API_CONTRACT.md
前端 OpenAPI 生成类型和 API client
```

## 契约规则

```text
所有 API Request / Response 必须使用 Pydantic V2 模型。
后端必须暴露 /openapi.json。
前端必须从 OpenAPI 生成 TypeScript types、API client 类型约束、mock response 类型约束。
禁止前端手写后端 Response 类型。
禁止后端返回裸 dict 给业务层扩散。
禁止 mock 数据字段和真实接口字段不一致。
```

## Mock / Real 切换

```text
外部依赖必须可以 mock。
切换 mock/real 时，不允许改页面代码。
mock 和 real 必须使用同一套 Pydantic / OpenAPI 类型。
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
