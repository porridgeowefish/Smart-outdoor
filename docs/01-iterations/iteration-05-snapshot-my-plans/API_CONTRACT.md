# API Contract

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: Pydantic V2 schemas and `/openapi.json`.

## POST /api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save

用途：保存候选为规划快照。

Request:

```text
当前无 request body。
```

Response:

```json
{
  "snapshot_id": "snap_123",
  "continue_trip_plan_id": "tp_123",
  "source_candidate_id": "cand_1",
  "route": {
    "route_id": "route_1",
    "name": "四姑娘山大峰",
    "location": "四川省 · 阿坝藏族羌族自治州",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "cover_image_url": null,
    "display_tags": ["雪山", "自驾友好"],
    "track_preview": {
      "format": "geojson",
      "coordinate_system": "wgs84",
      "point_count": 120,
      "geojson": {"type": "LineString", "coordinates": [[102.9, 31.0], [102.91, 31.01]]}
    }
  },
  "advantage_tags": ["综合匹配", "雪山", "一日友好"],
  "recommendation_reason": "线路距离和爬升适合作为候选评估。",
  "score_breakdown": {},
  "planning_detail": {
    "summary": "这是一条可作为本次出行候选的线路。"
  },
  "evidence": {
    "weather": {"status": "unconfirmed"},
    "transport": {"status": "unconfirmed"},
    "web_evidence": {"status": "unconfirmed"}
  },
  "created_at": "2026-05-08T12:30:00+00:00"
}
```

错误码：

```text
CANDIDATE_ROUTE_NOT_FOUND
ROUTE_PLAN_SNAPSHOT_EXISTS
```

## GET /api/my/route-plan-snapshots

用途：获取当前用户保存的规划快照列表。

Query:

```text
当前无分页、status 或 keyword 查询参数。
```

Response:

```json
{
  "items": [
    {
      "snapshot_id": "snap_123",
      "continue_trip_plan_id": "tp_123",
      "source_candidate_id": "cand_1",
      "route": {
        "route_id": "route_1",
        "name": "四姑娘山大峰",
        "location": "四川省 · 阿坝藏族羌族自治州",
        "distance_km": 15.2,
        "elevation_gain_m": 1320,
        "cover_image_url": null,
        "display_tags": ["雪山", "自驾友好"],
        "track_preview": null
      },
      "advantage_tags": ["综合匹配", "雪山"],
      "recommendation_reason": "线路距离和爬升适合作为候选评估。",
      "created_at": "2026-05-08T12:30:00+00:00"
    }
  ],
  "total": 1
}
```

## GET /api/my/route-plan-snapshots/{snapshot_id}

用途：查看保存时刻的规划详情。

Response:

```json
{
  "snapshot_id": "snap_123",
  "continue_trip_plan_id": "tp_123",
  "source_candidate_id": "cand_1",
  "route": {
    "route_id": "route_1",
    "name": "四姑娘山大峰",
    "location": "四川省 · 阿坝藏族羌族自治州",
    "distance_km": 15.2,
    "elevation_gain_m": 1320,
    "cover_image_url": null,
    "display_tags": ["雪山", "自驾友好"],
    "track_preview": null
  },
  "advantage_tags": ["综合匹配", "雪山"],
  "recommendation_reason": "线路距离和爬升适合作为候选评估。",
  "score_breakdown": {},
  "planning_detail": {
    "summary": "这是一条可作为本次出行候选的线路。",
    "risk_notes": ["近期路况未确认，出发前需要再次核实。"]
  },
  "evidence": {
    "weather": {"status": "unconfirmed"},
    "transport": {"status": "unconfirmed"},
    "web_evidence": {"status": "unconfirmed"}
  },
  "created_at": "2026-05-08T12:30:00+00:00"
}
```

当前响应不包含：

```text
user_note
share_text
saved_at
actions
```

前端跳转：

```text
response.route.route_id 可用于跳转线路资产详情：
GET /api/routes/{route_id}
```

错误码：

```text
ROUTE_PLAN_SNAPSHOT_NOT_FOUND
```

设计边界：

```text
点击候选详情不创建 snapshot
点击保存才创建 snapshot
snapshot.route 是保存时复制的 route_summary，不随 route_asset 后续变化自动变化
snapshot.route.route_id 仍指向原 route_asset，可进入线路本体详情
snapshot.planning_detail / evidence 是保存时复制的候选详情内容
详情可以通过 continue_trip_plan_id 回到来源 TripPlan
```
