from __future__ import annotations


def waiting_user_content() -> str:
    return (
        "我先确认两个关键信息：交通方式你更倾向自驾还是公共交通？"
        "这次想轻松一点，还是接受中等强度？"
    )


def recommendation_content(candidate_count: int = 3) -> str:
    return (
        f"我按你的出发地、交通方式和强度偏好，先从线路库里筛了 {candidate_count} 条候选。"
        "天气、交通和近期路况目前是 mock 证据，出发前还需要核实。"
    )
