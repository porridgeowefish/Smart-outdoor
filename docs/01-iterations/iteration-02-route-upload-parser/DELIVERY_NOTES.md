# Delivery Notes

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: implementation notes; upload contract superseded by Iteration 07.

## 交付内容

- 上传 / 解析链路落地：`backend/app/features/routes/{router,service,parser,model,schemas}.py`。
- 三张表 `route_assets` / `route_files` / `route_analysis_snapshots`（见 ORM model）。
- GPX / KML（含 gx:Track）/ GeoJSON（LineString / MultiLineString）解析。
- 距离、爬升 / 下降、最低 / 最高海拔、起终点、bounds、center、track_geojson、静止停留扣除的 moving_time。
- 解析失败保留资产与文件，标记 `parse_status=failed` + `parse_error=TRACK_PARSE_FAILED`。
- 测试：`backend/tests/routes/test_route_upload_api.py`、`backend/tests/routes/test_track_parser.py`。

## 测试运行

```powershell
$env:DATABASE_URL='sqlite:///./test_iter2_tmp.db'
python -m pytest backend/tests/routes/test_route_upload_api.py backend/tests/routes/test_track_parser.py
```

```text
23 passed in 6.75s
```

> 上传测试覆盖 iter07 后的 JSON complete 形态（前端直传 + storage_key）；multipart 形态已被 iter07 取代。

## 遗留风险

- 上传契约已被 iter07 取代（multipart → JSON metadata complete + 对象存储 / 前端直传）；本文保留历史边界，最新上传契约见 iter07。
- `steep_ratio` 当前实现恒为 null，未真正计算陡坡占比。
- 历史迭代，未记录：本轮上线日期、原 multipart 上传测试的当时通过情况。
