# Test Plan

Status: superseded (API 见 Iteration 07)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: backend tests。

## Service / Unit

- [US-03.1] display_tags 由 manual_tags 扁平化生成，最多取 3 个。
- [US-03.1] location 优先取 analysis_json.location.display_name，否则回退 manual_tags，否则 "待识别"。
- [US-03.1] track_preview 由 build_track_preview 从 track_geojson 派生。
- [US-03.1] 无 analysis 的线路不破坏列表响应（跳过该条或返回降级字段）。
- [US-03.1] 距离/爬升范围过滤在内存中执行；分页 total 反映过滤后结果。

## API

- [US-03.1] 默认返回 public + 当前用户 private。
- [US-03.1] 不返回其他用户 private。
- [US-03.1] visibility=public 只返回 public；visibility=private 只返回当前用户 private。
- [US-03.1] tags 筛选 any 命中任一即返回；筛选 all 须全命中。
- [US-03.1] GET /api/routes/tag-taxonomy 返回标签分类。
- [US-03.1] 列表返回 location 与 track_preview。
- [US-03.2] 详情返回 analysis、track、primary_file、actions。
- [US-03.2] private 详情仅创建者本人可查看；他人访问返回 404。

## 权限

- [US-03.1] 未登录访问 /api/routes 返回 401。
- [US-03.2] 未登录访问 /api/routes/{route_id} 返回 401。
- [US-03.2] 用户访问他人 private 线路详情 → 404 ROUTE_NOT_FOUND。

## 失败路径

- [US-03.2] route_id 不存在 → 404 ROUTE_NOT_FOUND。

## 验证命令

```powershell
pytest tests/routes
```

## 历史来源

- backend/tests/routes（实际测试路径以仓库为准）
