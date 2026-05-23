from __future__ import annotations

from typing import Any


CHOICE_WRITABLE_FIELDS = {
    "activity_goal",
    "departure_area",
    "time_window",
    "transport_hint",
    "terrain_tolerance",
    "safety_priority",
    "preference_tags",
    "avoid_tags",
    "scenery_preferences",
    "supply_requirement",
    "ability_hint",
}

CORE_REQUIRED_FIELDS = [
    "activity_goal",
    "departure_area",
    "time_window",
    "transport_hint",
]

FIELD_LABELS = {
    "activity_goal": "目标",
    "departure_area": "出发地",
    "time_window": "时间",
    "transport_hint": "交通",
    "terrain_tolerance": "路况接受度",
    "safety_priority": "安全优先级",
    "preference_tags": "偏好",
    "avoid_tags": "避开",
    "scenery_preferences": "风景",
    "supply_requirement": "补给",
    "ability_hint": "强度偏好",
}

DISPLAY_VALUES = {
    "self_drive": "自驾",
    "public_transport": "公共交通",
    "flexible": "都可以，帮我权衡",
    "avoid_icy_road": "尽量避开冰雪路",
    "accept_normal_trail": "接受常规山路",
    "safety_first": "安全优先",
    "balanced": "风景和安全平衡",
}

RISK_KEYWORDS = ("雪", "冰", "野路", "亲子", "新手", "安全", "危险")


def update_context_state(context_state: dict, content: str) -> dict:
    state = dict(context_state or {})
    lowered = content.lower()
    if "雪山" in content:
        state["activity_goal"] = "看雪山"
    elif "徒步" in content or "走走" in content:
        state.setdefault("activity_goal", "徒步")
    if "成都" in content:
        state["departure_area"] = "成都"
    if "自驾" in content:
        state["transport_hint"] = "self_drive"
    elif "公共交通" in content:
        state["transport_hint"] = "public_transport"
    elif "大巴" in content or "客车" in content:
        state["transport_hint"] = "bus"
    elif "高铁" in content or "城际" in content:
        state["transport_hint"] = "rail_plus_car"
    elif "飞机" in content:
        state["transport_hint"] = "flight_plus_car"
    if "一天" in content or "一日" in content or "周末" in content:
        state["time_window"] = {"raw_text": "一日或周末", "duration_days": 1}
    if "轻松" in content:
        state["ability_hint"] = {"level": "beginner"}
    elif "中等" in content or "中等强度" in content:
        state["ability_hint"] = {"level": "normal"}
    elif "挑战" in content or "强度" in lowered:
        state["ability_hint"] = {"level": "strong"}
    return state


def merge_text_context_state(existing_state: dict, extracted_state: dict, content: str) -> dict:
    state = dict(existing_state or {})
    field_sources = dict(state.get("field_sources") or {})
    extracted = dict(extracted_state or {})
    for field, value in extracted.items():
        if field in {"confirmed_fields", "missing_fields", "field_sources"}:
            continue
        source = field_sources.get(field)
        if source == "user_choice" and not _text_explicitly_mentions_field(field, content):
            continue
        state[field] = value
        field_sources[field] = (
            "user_explicit_text"
            if _text_explicitly_mentions_field(field, content)
            else "ai_extracted"
        )
    state["field_sources"] = field_sources
    state["missing_fields"] = missing_context_fields(state)
    return state


def merge_choice_answers(context_state: dict, answers: list[Any]) -> dict:
    state = dict(context_state or {})
    field_sources = dict(state.get("field_sources") or {})
    confirmed_fields = list(state.get("confirmed_fields") or [])
    for answer in answers:
        data = answer.model_dump() if hasattr(answer, "model_dump") else dict(answer)
        field = data.get("field")
        if field not in CHOICE_WRITABLE_FIELDS:
            raise ValueError(f"Unsupported choice field: {field}")
        value = data.get("custom_text") or data.get("value")
        state[field] = _normalize_choice_value(field, value)
        field_sources[field] = "user_choice"
        if field not in confirmed_fields:
            confirmed_fields.append(field)
    state["field_sources"] = field_sources
    state["confirmed_fields"] = confirmed_fields
    state["missing_fields"] = missing_context_fields(state)
    return state


def missing_context_fields(context_state: dict) -> list[str]:
    state = context_state or {}
    missing = [field for field in CORE_REQUIRED_FIELDS if not state.get(field)]
    if not missing and has_risk_context(state) and not (
        state.get("terrain_tolerance") or state.get("safety_priority")
    ):
        missing.append("terrain_tolerance")
    return missing


def has_risk_context(context_state: dict) -> bool:
    haystack = " ".join(
        [
            str(context_state.get("activity_goal") or ""),
            " ".join(_as_list(context_state.get("preference_tags"))),
            " ".join(_as_list(context_state.get("avoid_tags"))),
            " ".join(_as_list(context_state.get("scenery_preferences"))),
        ]
    )
    return any(keyword in haystack for keyword in RISK_KEYWORDS)


def confirmed_context(context_state: dict) -> dict:
    state = context_state or {}
    confirmed_fields = state.get("confirmed_fields") or []
    items = []
    for field in confirmed_fields:
        if field in state:
            items.append(
                {
                    "field": field,
                    "label": FIELD_LABELS.get(field, field),
                    "value": display_context_value(field, state[field]),
                }
            )
    return {"items": items}


def context_summary(context_state: dict, content: str) -> str:
    parts = []
    if context_state.get("departure_area"):
        parts.append(f"从{context_state['departure_area']}出发")
    if context_state.get("activity_goal"):
        parts.append(str(context_state["activity_goal"]))
    if context_state.get("transport_hint") == "self_drive":
        parts.append("自驾")
    if context_state.get("ability_hint"):
        parts.append(
            "中等强度"
            if context_state["ability_hint"].get("level") == "normal"
            else "有强度偏好"
        )
    return "，".join(parts) or content[:80]


def display_context_value(field: str, value: Any) -> str:
    if isinstance(value, dict):
        if field == "time_window":
            return str(value.get("raw_text") or value.get("duration_days") or value)
        if field == "ability_hint":
            return str(value.get("raw_text") or value.get("level") or value)
        return str(value)
    if isinstance(value, list):
        return "、".join(str(DISPLAY_VALUES.get(str(item), item)) for item in value)
    return str(DISPLAY_VALUES.get(str(value), value))


def _normalize_choice_value(field: str, value: Any) -> Any:
    if field == "time_window" and isinstance(value, str):
        return {"raw_text": value}
    if field == "ability_hint" and isinstance(value, str):
        return {"raw_text": value}
    return value


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def _text_explicitly_mentions_field(field: str, content: str) -> bool:
    checks = {
        "departure_area": ("成都", "深圳", "北京", "上海", "广州", "杭州", "出发"),
        "activity_goal": ("徒步", "走走", "雪", "露营", "亲子", "日出", "训练", "挑战"),
        "time_window": ("今天", "明天", "周末", "一天", "一日", "两天", "时间"),
        "transport_hint": ("自驾", "公共交通", "大巴", "客车", "高铁", "城际", "飞机"),
        "ability_hint": ("轻松", "中等", "强度", "挑战"),
        "terrain_tolerance": ("冰雪路", "野路", "路况", "危险"),
        "safety_priority": ("安全", "危险", "稳妥"),
    }
    return any(keyword in content for keyword in checks.get(field, ()))
