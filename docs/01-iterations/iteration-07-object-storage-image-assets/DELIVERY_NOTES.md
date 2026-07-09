# Delivery Notes

Status: active
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation, generated OpenAPI, and this iteration document set.

## 交付内容

- 统一 StorageService（local / cos 双 provider），COS 通过 `qcloud-cos-python-sdk-v5` 接入，local provider 保留为开发/测试默认。
- 前端通过临时凭据直传；图片前端压缩，后端不接收原图。
- 路线原始轨迹文件直传后由后端按 storage_key 读取并解析。
- 完整派生 track_geojson 存对象存储；高保真 track_preview_geojson 存数据库。
- preview 使用 Douglas-Peucker，tolerance_m=10，max_segment_length_m=150。
- `/api/routes/upload` 由 multipart/form-data 改为 JSON metadata complete。
- 头像上传改用 display/thumbnail variants + `PATCH /api/me`。
- 路线详情先渲染 preview，再通过 `GET /api/routes/{route_id}/track` 加载完整派生轨迹。
- 遗留资产迁移脚本 `backend/scripts/migrate_assets_to_cos.py` + 云封装 `scripts/run_cloud_asset_migration.py`。
- 云端对象存储冒烟脚本 `scripts/verify_cloud_object_storage_smoke.py`。
- 事件记录：[INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md](./INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md)（CORS 事故，独立保留，不在本文件复述）。

## 测试运行

```powershell
cd backend; python -m pytest
```

```text
104 passed
```

```powershell
npm run lint
```

```text
tsc --noEmit passed
```

云端对象存储冒烟（2026-05-18 / 2026-05-19）：

```powershell
python scripts/verify_cloud_object_storage_smoke.py
```

## 遗留风险

- COS 运行期需配置 `STORAGE_PROVIDER=cos` 与 `COS_SECRET_ID` / `COS_SECRET_KEY` / `COS_BUCKET` / `COS_REGION`（可选 `COS_TOKEN` / `COS_CDN_BASE_URL`）；后端从 `backend/.env` 加载，是本地与云的唯一运行配置事实源。
- `backend/config/app.local.env` 仅作可选实验回退，不作为第二份运行配置维护；`SMART_OUTDOOR_ENV_FILE` 仅用于临时诊断。
- 真实 config 文件与 `deploy_cloud.py` 被 git 忽略。
- `route_analysis_snapshots.track_geojson` 仍为 legacy 兼容字段；新数据不再把 full track_geojson 写入该字段。
- 本轮不引入消息队列/真实云函数触发；`avatar_processing_status`/`cover_processing_status` 只在本轮写 `ready`/`failed`，为后续异步化预留。

## 对齐与决策

### 2026-05-15 架构定稿

本轮将文件上传改为两阶段：阶段 A 前端向后端申请临时上传凭据；阶段 B 前端直传后把 url/storage_key/variants metadata 提交给业务接口 complete。旧 `POST /api/routes/upload` multipart 契约直接替换，不保留并行 legacy 上传接口。

```text
图片：数据库保存处理后版本 variants metadata，不保存上传原图。
原始轨迹：对象存储完整保存，数据库保存定位、checksum 和 metadata。
派生轨迹：full track_geojson 存对象存储，preview track_geojson 存数据库。
方案 C：preview 用 Douglas-Peucker（tolerance_m=10，max_segment_length_m=150），不使用最多 80 点硬限制。
provider：本地开发用 local；云部署用腾讯云 COS（object_storage 作为抽象别名，运行期归一为 cos）。
本轮不新增统一 file_assets 表；如后续需统一审计/清理/生命周期管理，再新增表并写 ADR。
本轮不新增 storage_upload_intents 持久化表；凭据由 provider 生成并带过期时间。
```

### 2026-05-18 Legacy Data Migration

迁移脚本 `backend/scripts/migrate_assets_to_cos.py`，云封装 `scripts/run_cloud_asset_migration.py`。

Dry run：

```powershell
cd backend; python scripts/migrate_assets_to_cos.py
```

Apply：

```powershell
cd backend; python scripts/migrate_assets_to_cos.py --apply
```

脚本默认读 `backend/.env`，Apply 前需设置：

```text
STORAGE_PROVIDER=cos
COS_SECRET_ID=...
COS_SECRET_KEY=...
COS_BUCKET=...
COS_REGION=...
```

若脚本在云服务器外运行、legacy `/static/...` 仅通过部署后端可达，传 `--base-url https://your-api-domain --apply`。

经 SSH 对部署的 Docker Compose 栈执行迁移：

```powershell
python scripts/run_cloud_asset_migration.py --rebuild
python scripts/run_cloud_asset_migration.py --rebuild --apply
```

封装读环境变量 `ECS_HOST` / `ECS_USER` / `ECS_PASSWORD` 或 `ECS_KEY_FILE` / `SMART_OUTDOOR_REMOTE_DIR`。运行期配置归 `backend/.env`，不为迁移/部署重建单独的 `backend/.env.production`。

迁移范围：

```text
route_files：legacy 原始 GPX/KML/GeoJSON 上传到 COS，更新存储 metadata。
route_analysis_snapshots：legacy track_geojson 作为 full 派生 GeoJSON 上传到 COS，回填 preview metadata。
users：legacy avatar_url 图片上传到 COS，回填 avatar variants metadata。
route_assets：legacy cover_image_url 图片上传到 COS，回填 cover variants metadata。
```

2026-05-18 云端迁移校验：

```text
route_files migrated to COS: 10 / 10
derived track_geojson files migrated to COS: 10 / 10
route cover images migrated to COS: 9 / 9
user avatars migrated to COS: 1 / 1
```

2026-05-18 云端运行验证：

```text
frontend public entry: 200
GET /api/routes: 200
GET /api/routes/{route_id}: 200
GET /api/routes/{route_id}/track: 200
COS cover image fetch through returned naked URL with allowed Referer: 200 image/jpeg
COS cover image fetch with empty Referer: 403
COS cover image fetch with untrusted Referer: 403
sample full track point_count: 20647
```

### 2026-05-18 Cloud Hotfix（运行期访问模型）

运行期访问模型为 public-read COS bucket + Referer 防盗链。后端对路线封面/路线文件/头像返回裸 COS 公网 URL，因此 COS Referer 规则会拦截空/非可信浏览器请求。上传 URL 仍为 signed PUT（前端直传需临时写权限）。

2026-05-18 校验的 COS 配置：

```text
bucket ACL: public-read
Referer type: White-List
allowed Referers: 部署服务器 IP 与 80 端口变体
empty Referer: Deny
```

### 2026-05-19 Upload CORS Incident Follow-Up

事件记录：[INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md](./INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md)。

根因：前端直传用 signed COS PUT URL，但 bucket 无 CORS 规则，浏览器 OPTIONS 预检 403；后端/local provider 测试仍通过。

2026-05-19 校验的云端修复：

```text
COS CORS AllowedOrigin: 部署前端域名与 :80 变体
COS CORS AllowedMethod: PUT, GET, HEAD
COS CORS AllowedHeader: *
COS CORS ExposeHeader: ETag, x-cos-request-id, x-cos-trace-id
COS CORS MaxAgeSeconds: 600
POST /api/storage/upload-credentials: 200
OPTIONS signed PUT upload_url: 200
signed PUT route track probe object: 200
signed PUT avatar probe object: 200
empty Referer read: 403
untrusted Referer read: 403
allowed Referer read: 200
```

## 暴露的权衡

- 两阶段上传 + 前端压缩：降低后端带宽/CPU，代价是浏览器侧 CORS/Referer/签名链路需云端独立冒烟（TestClient 不足以闭环）。
- 方案 C（DB preview + 对象存储 full track）：列表/详情初屏快，但 full track 需二次请求；`track_geojson` 字段保留为 legacy 兼容。
- 本轮不新增统一 file_assets 表：避免一次性重构过大，代价是头像/封面/轨迹/分析各自维护存储字段。
- `object_storage` 作为抽象 provider 名，运行期归一为 `cos`：保持业务契约稳定，迁移/落地记录可用 `cos`。

> 契约级字段类型与错误码见 API_CONTRACT 与 DATABASE_DESIGN，不在本文件重复。
