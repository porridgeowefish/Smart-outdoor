from __future__ import annotations

from typing import Any


ABSOLUTE_CLAIMS = (
    "放心去",
    "一定适合",
    "绝对安全",
    "肯定没问题",
)

RECENT_CONDITION_CLAIMS = (
    "近期路况良好",
    "路况很好",
    "最近很多人走过",
    "没有封路",
    "没有封山",
)


def evaluate_candidate_output(planning_detail: dict, evidence: dict) -> dict[str, Any]:
    text = _planning_text(planning_detail)
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for phrase in ABSOLUTE_CLAIMS:
        if phrase in text:
            issues.append(
                {
                    "field": "planning_detail",
                    "type": "absolute_claim",
                    "message": f"包含不允许的绝对化表达：{phrase}",
                }
            )

    if any(phrase in text for phrase in RECENT_CONDITION_CLAIMS) and not _has_confirmed_web_evidence(
        evidence
    ):
        issues.append(
            {
                "field": "planning_detail",
                "type": "unsupported_recent_condition",
                "message": "近期路况或实走记录结论需要 confirmed Web 证据支持。",
            }
        )

    _append_evidence_warnings(evidence, warnings)
    return {
        "passed": not issues,
        "issues": issues,
        "warnings": warnings,
    }


def _planning_text(planning_detail: dict) -> str:
    chunks: list[str] = []
    for value in planning_detail.values():
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, list):
            chunks.extend(str(item) for item in value)
    return "\n".join(chunks)


def _has_confirmed_web_evidence(evidence: dict) -> bool:
    web_evidence = evidence.get("web_evidence")
    if not isinstance(web_evidence, dict):
        return False
    sources = web_evidence.get("sources")
    has_source_url = isinstance(sources, list) and any(
        isinstance(source, dict) and source.get("url") for source in sources
    )
    return web_evidence.get("status") == "confirmed" and has_source_url


def _append_evidence_warnings(evidence: dict, warnings: list[dict[str, str]]) -> None:
    weather = evidence.get("weather")
    if not isinstance(weather, dict) or weather.get("status") != "confirmed":
        warnings.append(
            {
                "field": "evidence.weather",
                "type": "weather_unconfirmed",
                "message": "天气不是 confirmed 状态，回复中只能保守表达。",
            }
        )

    transport = evidence.get("transport")
    if not isinstance(transport, dict) or transport.get("status") != "confirmed":
        warnings.append(
            {
                "field": "evidence.transport",
                "type": "transport_unconfirmed",
                "message": "交通不是 confirmed 状态，回复中只能保守表达。",
            }
        )

    web_evidence = evidence.get("web_evidence")
    if not isinstance(web_evidence, dict) or web_evidence.get("status") != "confirmed":
        warnings.append(
            {
                "field": "evidence.web_evidence",
                "type": "web_evidence_limited",
                "message": "近期公开证据不足，不能断言近期路况。",
            }
        )
