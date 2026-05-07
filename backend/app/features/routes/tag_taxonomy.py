from __future__ import annotations

from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset
from app.features.routes.service import display_tags_from_manual_tags

TAG_TAXONOMY: dict[str, dict[str, list[str] | str]] = {
    "supply": {
        "label": "补给类型",
        "tags": [
            "有小卖部",
            "有餐饮点",
            "有饮用水",
            "有商店",
            "无补给（需背包自备）",
            "装备租赁",
            "有山泉",
        ],
    },
    "transport_facility": {
        "label": "交通设施",
        "tags": ["停车场", "公交站", "地铁站", "摆渡车", "自驾友好"],
    },
    "basic_service": {
        "label": "基础服务",
        "tags": ["卫生间", "医疗点", "救援点", "缆车", "观景台"],
    },
    "signal": {
        "label": "通信状态",
        "tags": ["基本有信号", "部分信号", "大部分信号弱", "无信号"],
    },
    "escape": {
        "label": "下撤点情况",
        "tags": ["无下撤点", "1个下撤点", "多个下撤点", "沿途可下撤"],
    },
    "safety_sign": {
        "label": "安全标识",
        "tags": ["有路标", "无路标或路标数量稀少"],
    },
    "audience": {
        "label": "场景人群",
        "tags": [
            "情侣友好",
            "团建友好",
            "摄影友好",
            "夜爬友好",
            "露营友好",
            "亲子友好",
            "宠物友好",
        ],
    },
    "terrain": {
        "label": "路况与地形",
        "tags": [
            "公路/铺装路",
            "石板平路",
            "土路/机耕路",
            "台阶路/阶梯路",
            "碎石路/乱石路",
            "泥泞/湿滑路",
            "野路（无明显路径）",
            "冰雪路",
            "特殊路况",
        ],
    },
    "scenery": {
        "label": "风光与场景",
        "tags": [
            "森林",
            "竹林",
            "原始森林",
            "栈道",
            "溪流",
            "河流",
            "海子",
            "大海",
            "湖泊",
            "瀑布",
            "沙滩",
            "温泉",
            "峡谷",
            "云海",
            "日出",
            "日落",
            "星空",
            "雪山",
            "冰川",
            "古镇",
            "历史古迹",
            "寺庙",
            "网红打卡点",
            "田园",
            "花海",
            "果园",
            "牧场",
            "牛羊",
            "马",
        ],
    },
    "scenic_management": {
        "label": "线路是否有景区运营管理",
        "tags": ["是", "否"],
    },
}

CONTEXT_SYNONYMS: dict[str, list[str]] = {
    "有小卖部": ["小卖部", "买水", "买吃的"],
    "有餐饮点": ["餐饮", "吃饭", "饭店", "餐厅"],
    "有饮用水": ["饮用水", "补水", "水源"],
    "无补给（需背包自备）": ["无补给", "自备", "背包自备"],
    "装备租赁": ["装备租赁", "租装备"],
    "有山泉": ["山泉"],
    "停车场": ["停车", "停车场"],
    "公交站": ["公交", "公交站"],
    "地铁站": ["地铁", "地铁站"],
    "摆渡车": ["摆渡车", "接驳车"],
    "自驾友好": ["自驾", "开车"],
    "卫生间": ["厕所", "卫生间"],
    "医疗点": ["医疗", "医务"],
    "救援点": ["救援"],
    "缆车": ["缆车", "索道"],
    "观景台": ["观景台"],
    "基本有信号": ["有信号", "信号好"],
    "部分信号": ["部分信号"],
    "大部分信号弱": ["信号弱"],
    "无信号": ["无信号", "没信号"],
    "无下撤点": ["无下撤", "不能下撤"],
    "1个下撤点": ["一个下撤", "1个下撤"],
    "多个下撤点": ["多个下撤"],
    "沿途可下撤": ["沿途下撤", "随时下撤"],
    "有路标": ["路标", "标识清楚"],
    "无路标或路标数量稀少": ["无路标", "路标少", "容易迷路"],
    "情侣友好": ["情侣"],
    "团建友好": ["团建"],
    "摄影友好": ["摄影", "拍照", "出片"],
    "夜爬友好": ["夜爬"],
    "露营友好": ["露营"],
    "亲子友好": ["亲子", "小朋友", "带娃"],
    "宠物友好": ["宠物", "狗"],
    "公路/铺装路": ["公路", "铺装"],
    "石板平路": ["石板"],
    "土路/机耕路": ["土路", "机耕路"],
    "台阶路/阶梯路": ["台阶", "阶梯"],
    "碎石路/乱石路": ["碎石", "乱石"],
    "泥泞/湿滑路": ["泥泞", "湿滑"],
    "野路（无明显路径）": ["野路", "无明显路径"],
    "冰雪路": ["冰雪", "结冰"],
    "森林": ["森林", "森系"],
    "竹林": ["竹林"],
    "原始森林": ["原始森林"],
    "栈道": ["栈道"],
    "溪流": ["溪流", "溯溪"],
    "河流": ["河流"],
    "海子": ["海子"],
    "大海": ["大海", "海边"],
    "湖泊": ["湖泊", "湖"],
    "瀑布": ["瀑布"],
    "沙滩": ["沙滩"],
    "温泉": ["温泉"],
    "峡谷": ["峡谷"],
    "云海": ["云海"],
    "日出": ["日出", " sunrise"],
    "日落": ["日落"],
    "星空": ["星空"],
    "雪山": ["雪山", "看雪"],
    "冰川": ["冰川"],
    "古镇": ["古镇"],
    "历史古迹": ["古迹", "历史"],
    "寺庙": ["寺庙"],
    "网红打卡点": ["网红", "打卡"],
    "田园": ["田园"],
    "花海": ["花海"],
    "果园": ["果园"],
    "牧场": ["牧场"],
    "牛羊": ["牛羊"],
    "马": ["马"],
    "是": ["景区", "运营管理"],
    "否": ["非景区", "没人管理"],
}


def taxonomy_categories() -> list[dict[str, object]]:
    return [
        {"key": key, "label": str(value["label"]), "tags": list(value["tags"])}
        for key, value in TAG_TAXONOMY.items()
    ]


def all_taxonomy_tags() -> list[str]:
    tags: list[str] = []
    for value in TAG_TAXONOMY.values():
        tags.extend(str(item) for item in value["tags"])
    return tags


def route_tags(route: RouteAsset, analysis: RouteAnalysisSnapshot) -> set[str]:
    tags = set(display_tags_from_manual_tags(route.manual_tags or {}, limit=200))
    tags.update(_metric_tags(analysis))
    if "雪山" in tags:
        tags.add("看雪山")
    if "日出" in tags:
        tags.add("看日出")
    return tags


def context_preference_tags(context_state: dict) -> set[str]:
    tags: set[str] = set()
    raw_values: list[str] = []

    for key in ("activity_goal", "departure_area", "current_location", "transport_hint"):
        value = context_state.get(key)
        if isinstance(value, str):
            raw_values.append(value)
    for key in ("preference_tags", "avoid_tags"):
        value = context_state.get(key)
        if isinstance(value, list):
            raw_values.extend(str(item) for item in value)
    time_window = context_state.get("time_window")
    if isinstance(time_window, dict):
        raw_values.extend(str(value) for value in time_window.values())
    ability_hint = context_state.get("ability_hint")
    if isinstance(ability_hint, dict):
        raw_values.extend(str(value) for value in ability_hint.values())

    text = " ".join(raw_values)
    for canonical, synonyms in CONTEXT_SYNONYMS.items():
        if any(synonym and synonym in text for synonym in synonyms):
            tags.add(canonical)
    return tags


def _metric_tags(analysis: RouteAnalysisSnapshot) -> set[str]:
    tags: set[str] = set()
    distance = analysis.distance_km
    climb = analysis.elevation_gain_m
    climb_ratio = climb / max(distance, 0.1)

    if distance <= 8:
        tags.update({"短线", "半日"})
    elif distance <= 16:
        tags.update({"中线", "一日"})
    elif distance <= 28:
        tags.update({"长线", "一日"})
    else:
        tags.update({"超长线", "两日"})

    if climb <= 500:
        tags.update({"低爬升", "轻松"})
    elif climb <= 1500:
        tags.update({"中爬升", "标准"})
    else:
        tags.update({"高爬升", "困难"})

    if climb_ratio >= 90:
        tags.add("陡峭")
    if distance <= 10 and climb <= 500:
        tags.add("新手友好")
    if distance >= 22 or climb >= 1300:
        tags.add("挑战")
    return tags
