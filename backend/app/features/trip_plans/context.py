from __future__ import annotations


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
