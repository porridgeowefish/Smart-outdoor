# Acceptance Criteria

Status: superseded (API 见 Iteration 07)
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: acceptance checklist for Iteration 03.

- [US-03.1] 前端能在列表页看到线路卡片，卡片展示封面、名称、位置、距离、爬升、展示标签。
- [US-03.1] 列表卡片可用轨迹预览渲染小地图或路线轮廓。
- [US-03.1] 前端能获取标签分类，用于标签筛选。
- [US-03.1] 默认列表只出现 public 线路和当前用户自己的 private 线路。
- [US-03.1] 其他用户的 private 线路不出现在列表里。
- [US-03.2] 点击卡片能进入线路详情。
- [US-03.2] 详情页能拿到 GeoJSON 轨迹用于地图渲染。
- [US-03.2] 详情页能拿到可见性、主文件信息和 UI 能力标志。
- [US-03.2] 详情页不混入规划建议、天气或交通信息。

## 不验收为完成

- 本轮交付了下载、编辑或 send-to-trip-plan 接口（仅 actions 标志位允许存在）。
