# API Contract

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json`; current upload contract is Iteration 07.

> Superseded by Iteration 07: `POST /api/routes/upload` 的 multipart 文件上传契约在 Iteration 07 被替换为 JSON metadata complete（前端直传文件 + 后端读 storage_key）。当前文件保留 Iteration 02 历史交付边界，不再作为最新上传接口契约。

## POST /api/routes/upload

用途：上传 GPX / KML / GeoJSON 轨迹文件，生成线路资产。

Request（multipart/form-data）:

```text
file          required  轨迹文件，GPX / KML / GeoJSON
cover_image   optional  封面图，JPEG / PNG / WebP
name          required  线路名称
description   optional  线路描述
visibility    public / private，默认 private
manual_tags   JSON string，optional，须为 JSON object
```

Success Response:

```json
{
  "route_id": "route_123",
  "file_id": "file_123",
  "parse_status": "parsed"
}
```

Parse Failed Response:

```text
解析失败不返回 HTTP 错误，仍返回 200。
保留 route_asset 与 route_file，parse_status=failed，
不创建 route_analysis_snapshot。
```

```json
{
  "route_id": "route_123",
  "file_id": "file_123",
  "parse_status": "failed",
  "parse_error": "TRACK_PARSE_FAILED"
}
```

错误码:

```text
401 UNAUTHORIZED 未登录用户上传。
400 UNSUPPORTED_FILE_TYPE 轨迹文件类型不在 GPX / KML / GeoJSON。
400 UNSUPPORTED_COVER_IMAGE_TYPE 封面图类型不在 JPEG / PNG / WebP。
400 INVALID_MANUAL_TAGS manual_tags 非合法 JSON object。
```

## 历史来源

- [iteration-07 API_CONTRACT](../iteration-07-object-storage-image-assets/API_CONTRACT.md)（取代本轮上传契约）
- DATABASE_DESIGN.md（route_assets / route_files / route_analysis_snapshots）
