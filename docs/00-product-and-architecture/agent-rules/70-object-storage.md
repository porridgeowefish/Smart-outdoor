# 70 对象存储闭环

Status: active
Owner: project maintainer
Last reviewed: 2026-05-19
Source of truth: object storage upload/read validation rules.

## 读取入口

```text
docs/01-iterations/iteration-07-object-storage-image-assets/
backend/.env
docker-compose.yml
deploy_cloud.py
rebuilt.ps1 / rebuilt.cmd
```

## 核心纪律

```text
不能只用后端 TestClient 或 local provider 测试证明完成。
前端直传对象存储必须验证 ACL 或 bucket policy、CORS 预检和真实浏览器上传、Referer / 防盗链读策略、签名 URL 的读写行为。
如果上传链路使用 signed PUT URL，交付前必须至少验证一次浏览器等价预检。
云端验收必须同时覆盖读写两条链路。
不得把“API 测试通过 + 云端读取通过”误判为“对象存储上传闭环完成”。
前端直传完成后，必须验证业务 complete 接口确实写库，并在刷新后通过读取接口返回新 key / URL。
```

## Signed PUT 预检

```text
OPTIONS signed upload_url
Origin: 部署前端 origin
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: content-type
```

## 云端验收覆盖

```text
POST /api/storage/upload-credentials
前端或浏览器等价方式直传文件
上传完成后的业务 complete 接口
业务详情页可读取对象和渲染结果
空 Referer / 非白名单 Referer 的防盗链行为
```

## 部署配置不得被覆盖

```text
STORAGE_PROVIDER
COS_SECRET_ID / COS_SECRET_KEY / COS_TOKEN
COS_BUCKET / COS_REGION / COS_CDN_BASE_URL
```
