# API 调用资料速查

本文只记录后端未来实现 API Client 时需要的最小调用资料，不包含真实密钥，不包含 SDK 封装代码。真实密钥见 `PRIVATE_SECRETS.local.md`。

## 1. 和风天气 QWeather

统一约定：请求头或参数中使用 `QWEATHER_API_KEY`；API Host 使用 `WEATHER_DEVELOPER_HOST`。正式实现时必须配置超时、重试、错误码处理和响应 Pydantic 模型。

### 1.1 实时天气

- 用途：根据经纬度获取当前天气、温度、风力、湿度、观测时间。
- Endpoint：`https://{WEATHER_DEVELOPER_HOST}/v7/weather/now`
- Method：`GET`
- 必要参数：`location={lon},{lat}`、`key={QWEATHER_API_KEY}`
- 关键返回字段：`code`、`updateTime`、`now.temp`、`now.feelsLike`、`now.text`、`now.windDir`、`now.windScale`、`now.humidity`、`now.precip`、`now.vis`
- 后续函数建议签名：`get_current_weather(lon: float, lat: float) -> CurrentWeather`

### 1.2 逐日天气

- 用途：获取未来多日天气趋势，用于判断出行窗口和风险。
- Endpoint：`https://{WEATHER_DEVELOPER_HOST}/v7/weather/{days}d`
- Method：`GET`
- 必要参数：`location={lon},{lat}`、`key={QWEATHER_API_KEY}`；`days` 常用 `3d`、`7d`
- 关键返回字段：`daily.fxDate`、`daily.tempMax`、`daily.tempMin`、`daily.textDay`、`daily.textNight`、`daily.windScaleDay`、`daily.precip`、`daily.uvIndex`
- 后续函数建议签名：`get_daily_forecast(lon: float, lat: float, days: int = 7) -> list[DailyWeather]`

### 1.3 逐小时天气

- 用途：细化当天出发、返程、看日出等时间敏感判断。
- Endpoint：`https://{WEATHER_DEVELOPER_HOST}/v7/weather/{hours}h`
- Method：`GET`
- 必要参数：`location={lon},{lat}`、`key={QWEATHER_API_KEY}`；`hours` 常用 `24h`、`72h`
- 关键返回字段：`hourly.fxTime`、`hourly.temp`、`hourly.text`、`hourly.windScale`、`hourly.pop`、`hourly.precip`
- 后续函数建议签名：`get_hourly_forecast(lon: float, lat: float, hours: int = 24) -> list[HourlyWeather]`

### 1.4 地理位置查询

- 用途：将自然语言地点解析为经纬度和行政区，用于后续天气、交通和线路检索。
- Endpoint：`https://geoapi.qweather.com/v2/city/lookup`
- Method：`GET`
- 必要参数：`location={keyword}`、`key={QWEATHER_API_KEY}`
- 关键返回字段：`location.name`、`location.lon`、`location.lat`、`location.adm1`、`location.adm2`、`location.country`
- 后续函数建议签名：`lookup_qweather_location(keyword: str) -> list[GeoLocation]`

## 2. 高德地图 AMap

统一约定：参数中使用 `AMAP_API_KEY`。高德返回通常包含 `status`、`info`、`infocode`，实现时必须统一处理非成功状态。

### 2.1 地理编码

- 用途：地址转经纬度。
- Endpoint：`https://restapi.amap.com/v3/geocode/geo`
- Method：`GET`
- 必要参数：`address`、`key={AMAP_API_KEY}`；可选 `city`
- 关键返回字段：`geocodes.formatted_address`、`geocodes.location`、`geocodes.adcode`、`geocodes.city`
- 后续函数建议签名：`geocode(address: str, city: str | None = None) -> list[GeocodeResult]`

### 2.2 逆地理编码

- 用途：经纬度转结构化地址，辅助线路起终点展示。
- Endpoint：`https://restapi.amap.com/v3/geocode/regeo`
- Method：`GET`
- 必要参数：`location={lon},{lat}`、`key={AMAP_API_KEY}`
- 关键返回字段：`regeocode.formatted_address`、`regeocode.addressComponent`、`regeocode.pois`
- 后续函数建议签名：`reverse_geocode(lon: float, lat: float) -> ReverseGeocodeResult`

### 2.3 驾车路线

- 用途：估算自驾到轨迹起点的耗时、距离、过路费和可达性。
- Endpoint：`https://restapi.amap.com/v3/direction/driving`
- Method：`GET`
- 必要参数：`origin={lon},{lat}`、`destination={lon},{lat}`、`key={AMAP_API_KEY}`
- 关键返回字段：`route.paths.distance`、`route.paths.duration`、`route.paths.tolls`、`route.paths.steps.instruction`
- 后续函数建议签名：`get_driving_route(origin: Coordinate, destination: Coordinate) -> RouteTransitPlan`

### 2.4 步行路线

- 用途：估算城市内或景区接驳步行距离；不用于替代户外轨迹难度分析。
- Endpoint：`https://restapi.amap.com/v3/direction/walking`
- Method：`GET`
- 必要参数：`origin={lon},{lat}`、`destination={lon},{lat}`、`key={AMAP_API_KEY}`
- 关键返回字段：`route.paths.distance`、`route.paths.duration`、`route.paths.steps.instruction`
- 后续函数建议签名：`get_walking_route(origin: Coordinate, destination: Coordinate) -> RouteTransitPlan`

### 2.5 公交路线

- 用途：估算公共交通到达线路起点的可行性。
- Endpoint：`https://restapi.amap.com/v3/direction/transit/integrated`
- Method：`GET`
- 必要参数：`origin={lon},{lat}`、`destination={lon},{lat}`、`city`、`key={AMAP_API_KEY}`
- 关键返回字段：`route.transits.duration`、`route.transits.walking_distance`、`route.transits.segments.bus.buslines.name`、`route.transits.segments.railway.name`
- 后续函数建议签名：`get_transit_route(origin: Coordinate, destination: Coordinate, city: str) -> list[TransitPlan]`

### 2.6 周边搜索

- 用途：检索起点附近停车场、补给点、住宿、景区入口等 POI。
- Endpoint：`https://restapi.amap.com/v3/place/around`
- Method：`GET`
- 必要参数：`location={lon},{lat}`、`keywords` 或 `types`、`key={AMAP_API_KEY}`；可选 `radius`
- 关键返回字段：`pois.name`、`pois.type`、`pois.location`、`pois.address`、`pois.distance`
- 后续函数建议签名：`search_poi_around(center: Coordinate, keyword: str, radius_m: int = 3000) -> list[Poi]`

### 2.7 距离矩阵

- 用途：批量估算用户位置到多个候选线路起点的距离和时间，用于候选排序。
- Endpoint：`https://restapi.amap.com/v3/distance`
- Method：`GET`
- 必要参数：`origins={lon},{lat}|...`、`destination={lon},{lat}`、`type`、`key={AMAP_API_KEY}`
- 关键返回字段：`results.origin_id`、`results.dest_id`、`results.distance`、`results.duration`
- 后续函数建议签名：`get_distance_matrix(origins: list[Coordinate], destination: Coordinate, mode: TravelMode) -> list[DistanceMatrixItem]`

## 3. Tavily 搜索

统一约定：使用 `TAVILY_API_KEY`。在 Agent 中只作为外部证据补充，不作为线路主召回来源。搜索结果必须保存来源 URL、标题、摘要和检索时间，供证据浮层展示。

### 3.1 基础搜索

- 用途：查询路线近期路况、他人实走记录、交通变化、封山封路等开放信息。
- Endpoint：`https://api.tavily.com/search`
- Method：`POST`
- 必要参数：`api_key`、`query`
- 建议参数：`search_depth="basic"`、`max_results`、`include_answer=false`
- 关键返回字段：`query`、`results.title`、`results.url`、`results.content`、`results.score`
- 后续函数建议签名：`search_web(query: str, max_results: int = 5) -> list[WebEvidence]`

### 3.2 带上下文搜索

- 用途：让 Agent 围绕候选路线和用户需求做更聚焦的证据搜索，例如“某路线近期是否有人一日往返”。
- Endpoint：`https://api.tavily.com/search`
- Method：`POST`
- 必要参数：`api_key`、`query`
- 建议参数：`search_depth="advanced"`、`include_answer=true`、`include_raw_content=false`
- 关键返回字段：`answer`、`results.title`、`results.url`、`results.content`、`results.score`
- 后续函数建议签名：`search_web_with_context(query: str, context: SearchContext, max_results: int = 8) -> WebSearchResult`

## 4. LLM OpenAI-compatible

统一约定：使用 `LLM_API_KEY` 和 OpenAI-compatible Chat Completions 协议。模型名称、Base URL 应进入后续配置文件，不在业务逻辑中硬编码。

### 4.1 Chat Completions

- 用途：意图识别、上下文抽取、候选解释、风险总结、分享文本生成。
- Endpoint：`{LLM_BASE_URL}/chat/completions`
- Method：`POST`
- 必要 Header：`Authorization: Bearer {LLM_API_KEY}`、`Content-Type: application/json`
- 必要 Body：`model`、`messages`
- 建议 Body：`temperature`、`max_tokens`、`timeout`、`response_format`
- 关键返回字段：`choices[0].message.content`、`usage.prompt_tokens`、`usage.completion_tokens`
- 后续函数建议签名：`chat(messages: list[ChatMessage], response_format: ResponseFormat | None = None) -> ChatResult`

### 4.2 JSON 输出约束

- 用途：把自然语言需求稳定抽取为结构化上下文，例如出发地、时间、人数、交通方式、体能目标、风险偏好。
- Endpoint：`{LLM_BASE_URL}/chat/completions`
- Method：`POST`
- 必要 Header：`Authorization: Bearer {LLM_API_KEY}`、`Content-Type: application/json`
- 必要 Body：`model`、`messages`、`response_format={"type":"json_object"}` 或供应商兼容的 JSON Schema 参数
- 关键返回字段：`choices[0].message.content`，内容应可解析为 Pydantic V2 模型
- 后续函数建议签名：`extract_trip_context(messages: list[ChatMessage]) -> TripContextPatch`

## 5. 实现约束

- 所有 API Client 后续必须使用 Pydantic V2 输入输出模型，禁止在业务层传递原始 JSON 字典。
- 所有外部 API 调用必须有超时、重试和异常归一化。
- Agent Prompt 必须包含“仅基于已知信息，严禁捏造；无法确认时返回不确定并给出证据缺口”。
- Tavily 和 LLM 不能直接决定最终推荐，必须通过 Evaluator 检查证据充分性、用户能力匹配和安全风险。
