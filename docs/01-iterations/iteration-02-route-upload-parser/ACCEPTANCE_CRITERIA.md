# Acceptance Criteria

Status: superseded
Owner: project maintainer
Last reviewed: 2026-06-14
Source of truth: product acceptance for Iteration 02; upload contract superseded by Iteration 07.

- [US-02.1] 登录用户可以上传一条 GPX / KML / GeoJSON 轨迹并生成线路资产。
- [US-02.1] 系统拒绝不支持的轨迹文件类型。
- [US-02.1] 用户可选上传封面图，系统拒绝不支持的封面图类型。
- [US-02.1] 未登录用户不能上传。
- [US-02.2] 上传成功后，系统展示线路的距离、累计爬升和地图轨迹。
- [US-02.2] 解析失败时，系统仍保留线路和原始文件，并给出明确的失败提示，不展示空指标。
- [US-02.3] 用户上传时填写的标签能被保存并在后续查看时看到。
- [US-02.3] 标签内容必须是结构化对象，非对象输入被拒绝。
