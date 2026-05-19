# 40 TDD 与验证

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: testing and verification rules.

## TDD 要求

```text
每个 slice 先写测试，再写实现。
不允许先写大量实现，最后再补测试。
不能运行测试时，必须说明原因和剩余风险。
```

## 最低测试覆盖

```text
API 成功路径测试
API 失败路径测试
权限测试
关键 service 测试
轨迹解析测试
```

## 验证纪律

```text
改接口：验证 Schema、OpenAPI、API 文档和前端类型。
改表结构：验证 ORM model、数据库设计和测试。
改前端对接：验证生成类型、API client、mock response 与真实接口一致。
跳过验证必须在最终回复中说明原因。
```
