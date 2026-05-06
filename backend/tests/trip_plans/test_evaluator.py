from __future__ import annotations

from app.features.trip_plans.evaluator import evaluate_candidate_output


def test_evaluator_passes_cautious_output_with_unconfirmed_warnings() -> None:
    result = evaluate_candidate_output(
        planning_detail={
            "summary": "这条线路可以作为候选。",
            "risk_notes": ["近期路况未确认，出发前需要再次核实。"],
        },
        evidence={
            "weather": {"status": "unconfirmed"},
            "transport": {"status": "unconfirmed"},
            "web_evidence": {"status": "limited", "sources": []},
        },
    )

    assert result["passed"] is True
    assert result["issues"] == []
    assert {warning["type"] for warning in result["warnings"]} == {
        "weather_unconfirmed",
        "transport_unconfirmed",
        "web_evidence_limited",
    }


def test_evaluator_rejects_absolute_safety_language() -> None:
    result = evaluate_candidate_output(
        planning_detail={
            "summary": "这条线路一定适合你，可以放心去。",
            "risk_notes": [],
        },
        evidence={
            "weather": {"status": "confirmed"},
            "transport": {"status": "confirmed"},
            "web_evidence": {"status": "confirmed", "sources": [{"url": "https://example.com"}]},
        },
    )

    assert result["passed"] is False
    assert any(issue["type"] == "absolute_claim" for issue in result["issues"])


def test_evaluator_requires_confirmed_web_evidence_for_recent_condition_claims() -> None:
    result = evaluate_candidate_output(
        planning_detail={
            "summary": "这条线路近期路况良好，最近很多人走过。",
            "risk_notes": [],
        },
        evidence={
            "weather": {"status": "confirmed"},
            "transport": {"status": "confirmed"},
            "web_evidence": {"status": "limited", "sources": [{"url": "https://example.com"}]},
        },
    )

    assert result["passed"] is False
    assert any(issue["type"] == "unsupported_recent_condition" for issue in result["issues"])
