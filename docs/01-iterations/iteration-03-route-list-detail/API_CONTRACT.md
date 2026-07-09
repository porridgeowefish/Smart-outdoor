# API Contract

Status: superseded (Iteration 07)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: Pydantic V2 schemas and `/openapi.json`.

> Superseded by Iteration 07：`track_preview` 与详情轨迹契约在 Iteration 07 改为数据库高保真 preview + 对象存储 full track_geojson。本文件保留 Iteration 03 历史交付边界。

## 端点

| 方法 | 路径 | 本轮变化 |
|---|---|---|
| GET | `/api/routes` | 新增：列表 + 筛选 + 分页 |
| GET | `/api/routes/tag-taxonomy` | 新增：标签分类 |
| GET | `/api/routes/{route_id}` | 新增：线路详情 |

## 请求 / 响应示例

### GET /api/routes

Query：

```text
keyword: str
visibility: "public" | "private" | "all"   默认 all
min_distance_km: float
max_distance_km: float
min_elevation_gain_m: float
max_elevation_gain_m: float
tags: str
tag_match_mode: "any" | "all"             默认 any
page: int                                  默认 1
page_size: int                             默认 20
```

Response：

```json
{
  "items": [
    {
      "route_id": "route_1",
      "name": "四姑娘山大峰",
      "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
      "location": "四川省 · 阿坝藏族羌族自治州",
      "visibility": "public",
      "distance_km": 15.2,
      "elevation_gain_m": 1320,
      "manual_tags": {},
      "display_tags": ["雪山", "自驾友好"],
      "track_preview": {
        "format": "geojson",
        "coordinate_system": "wgs84",
        "point_count": 120,
        "geojson": {
          "type": "LineString",
          "coordinates": [[102.9, 31.0], [102.91, 31.01]]
        }
      }
    }
  ],
  "pagination": {"page": 1, "page_size": 20, "total": 1}
}
```

可见性规则：

```text
visibility=all      → public + 当前用户自己的 private
visibility=public   → 仅 public
visibility=private  → 仅当前用户自己的 private
其他用户的 private 永不返回
```

### GET /api/routes/tag-taxonomy

Response：

```json
{
  "categories": [
    {"key": "scenery", "label": "风光与场景", "tags": ["森林", "溪流", "雪山"]}
  ]
}
```

### GET /api/routes/{route_id}

Response：

```json
{
  "route_id": "route_1",
  "name": "四姑娘山大峰",
  "description": "经典雪山体验路线",
  "cover_image_url": "https://cdn.example.com/routes/route_1.jpg",
  "location": "四川省 · 阿坝藏族羌族自治州",
  "visibility": "public",
  "source_type": "user_upload",
  "source_name": null,
  "manual_tags": {"scenery": ["雪山"], "transport_facility": ["自驾友好"]},
  "analysis": {
    "route_analysis_snapshot_id": "analysis_1",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "elevation_loss_m": 1320,
    "elevation_min_m": 3200,
    "elevation_max_m": 5025,
    "climb_ratio": 86.8,
    "steep_ratio": null,
    "start_point": {"lon": 102.9, "lat": 31.0},
    "end_point": {"lon": 102.91, "lat": 31.01},
    "bounds": {"min_lon": 102.9, "min_lat": 31.0, "max_lon": 102.91, "max_lat": 31.01},
    "center_point": {"lon": 102.905, "lat": 31.005},
    "analysis_json": {}
  },
  "track_preview": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "point_count": 842,
    "geojson": {"type": "LineString", "coordinates": [[102.9, 31.0]]}
  },
  "track": {
    "format": "geojson",
    "coordinate_system": "wgs84",
    "source": "derived_full_geojson",
    "point_count": 842,
    "track_url": "/api/routes/route_1/track",
    "geojson": null
  },
  "primary_file": {
    "file_id": "file_1",
    "file_type": "gpx",
    "file_url": "/static/routes/route_1/file_1.gpx",
    "parse_status": "parsed"
  },
  "actions": {"can_send_to_trip_plan": true, "can_download_file": false, "can_edit": true}
}
```

详情字段说明：

```text
actions.can_send_to_trip_plan  本轮恒为 true，但本轮未实现 send-to-trip-plan API。
actions.can_download_file      本轮恒为 false，本轮未实现下载 API。
actions.can_edit               创建者或 admin 为 true，本轮未实现编辑 API。
track.geojson                  详情恒为 null；完整 geojson 由 GET /api/routes/{route_id}/track 取得。
```

详情不返回：规划建议 / 天气 / 交通 / snapshot 生成。

## 错误码

| HTTP | code | 触发 |
|---|---|---|
| 401 | AUTH_REQUIRED | 未登录访问（get_current_user 强制）。 |
| 404 | ROUTE_NOT_FOUND | route_id 不存在或当前用户无权查看（含他人 private）。 |

## 历史来源

- ../iteration-07-high-fidelity-track-preview/API_CONTRACT.md（超越本轮 track 契约）
- backend/app/features/routes/router.py、schemas.py
