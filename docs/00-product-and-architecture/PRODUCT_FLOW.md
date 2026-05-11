# 产品流程

Status: active
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: migrated from PRD UI flow and `design_doc` diagrams.

## MVP 主入口

```text
出去走走：对话式规划入口
我的规划：已保存方案卡
线路：线路资产浏览、上传、详情
个人中心：用户资料、活动轨迹、能力画像
```

## 核心规划流程

```text
用户表达模糊意图
↓
Agent 抽取上下文
↓
信息不足则自然追问
↓
信息充分则召回线路
↓
补充天气、交通、外部证据
↓
输出 3 张候选线路卡片
↓
用户点击候选查看详情
↓
用户保存到我的规划或继续追问
```

## 线路流程

来源图：

![线路展示流程图](../../../design_doc/线路展示流程图.png)

用户路径：

```text
进入线路 Tab
↓
浏览 / 搜索线路卡片
↓
点击线路详情
↓
查看轨迹地图、指标、标签和原始文件
↓
可转发到出去走走做规划
```

## 轨迹资产流程

来源图：

![轨迹资产相关流程图](../../../design_doc/轨迹资产相关流程图.png)

数据流：

```text
上传 KML / GPX / GeoJSON
↓
保存原始文件到 route_files
↓
解析距离、爬升、起终点、bounds、center_point
↓
生成简化 track_geojson
↓
写入 route_analysis_snapshots
↓
线路详情和 Agent 推荐都读取分析快照
```

## 个人中心与能力画像流程

来源图：

![个人信息流程图](../../../design_doc/个人信息流程图.png)

用户路径：

```text
进入个人中心
↓
查看用户资料
↓
上传已完成活动轨迹
↓
保存 activity_track
↓
解析活动指标
↓
更新 user_ability_profile
↓
Agent 推荐时读取能力画像
```

## 规划状态流程

来源图：

![一个规划的状态图](../../../design_doc/一个规划的状态图.png)

核心原则：

```text
TripPlan 是长期规划工作区
AgentRun 是每条用户消息触发的一次后台运行
候选线路不是快照
只有用户点击保存才创建 route_plan_snapshot
```

