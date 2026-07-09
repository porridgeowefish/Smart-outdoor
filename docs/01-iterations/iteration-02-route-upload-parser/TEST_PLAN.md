# Test Plan

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests; upload contract superseded by Iteration 07.

## Service / Unit

- [US-02.2] 解析 GPX → distance_km / elevation_gain_m / start_point / end_point / track_geojson。
- [US-02.2] 解析 GeoJSON LineString / MultiLineString 指标。
- [US-02.2] 解析 KML gx:Track 坐标与时间。
- [US-02.2] KML 同时含 LineString 与 gx:Track → 取点更多的来源。
- [US-02.2] 轨迹点数 < 2 → 抛 TRACK_PARSE_FAILED。
- [US-02.2] 稀疏轨迹按 10m 间距加密。
- [US-02.2] GPX 含静止停留 → 从 moving_time 中扣除 rest_time。
- [US-02.2] 上传成功 → 创建 route_asset / route_file / route_analysis_snapshot。
- [US-02.2] 解析失败 → route_file.parse_status=failed 且不创建 route_analysis_snapshot。
- [US-02.1] manual_tags 非 dict → 拒绝（INVALID_MANUAL_TAGS / 422）。

## API

- [US-02.1] 上传合法 GPX → 200，parse_status=parsed，落 route_asset / route_file / snapshot。
- [US-02.1] 上传合法 KML → 200，parse_status=parsed。
- [US-02.1] 上传合法 GeoJSON → 200，parse_status=parsed。
- [US-02.1] 上传合法封面图 → 写入 cover_image_url 与 variants。
- [US-02.1] 未登录上传 → 401 UNAUTHORIZED。
- [US-02.3] 多维 manual_tags 保存并可在详情读取。

## 失败路径

- [US-02.1] 不支持的轨迹文件类型 → 400 UNSUPPORTED_FILE_TYPE。
- [US-02.1] 不支持的封面图类型 / 无效 cover metadata → 400。
- [US-02.2] 损坏 / 空轨迹文件 → 200，parse_status=failed，parse_error=TRACK_PARSE_FAILED，不创建 snapshot。

## 验证命令

```powershell
$env:DATABASE_URL='sqlite:///./test_iter2_tmp.db'
pytest backend/tests/routes/test_route_upload_api.py backend/tests/routes/test_track_parser.py
```
