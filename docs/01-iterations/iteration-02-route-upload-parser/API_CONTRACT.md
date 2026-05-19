# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

> Superseded by Iteration 07: `POST /api/routes/upload` 的 multipart 文件上传契约在 Iteration 07 被直接替换为 JSON metadata complete。当前文件保留 Iteration 02 历史交付边界，不再作为最新上传接口契约。

## POST /api/routes/upload

用途：上传 KML / GPX / GeoJSON，生成线路资产。

Request:

```text
multipart/form-data
file: required
cover_image: optional, JPEG / PNG / WebP
name: required
description: optional
visibility: public / private, default private
manual_tags: JSON string, optional
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

解析失败不会返回 HTTP 错误。当前实现会保留 `route_asset` 和 `route_file`，返回 `parse_status = failed`，不创建 `route_analysis_snapshot`。

```json
{
  "route_id": "route_123",
  "file_id": "file_123",
  "parse_status": "failed",
  "parse_error": "TRACK_PARSE_FAILED"
}
```

错误码：

```text
UNSUPPORTED_FILE_TYPE
INVALID_MANUAL_TAGS
UNSUPPORTED_COVER_IMAGE_TYPE
```
