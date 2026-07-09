from __future__ import annotations

from fastapi.testclient import TestClient


def test_dimension_card_appears_when_intent_recalled(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "想简单轻松地走走"},
    )
    questions = response.json()["choice_request"]["questions"]
    fields = [question["field"] for question in questions]

    assert "intent_dimensions" in fields
    dimension_question = next(q for q in questions if q["field"] == "intent_dimensions")
    assert dimension_question["multi_select"] is True
    assert dimension_question["allow_custom"] is False
    values = {option["value"] for option in dimension_question["options"]}
    assert {"physical_ease", "terrain"} <= values
    assert len(dimension_question["question"]) <= 100


def test_subjective_dimension_writes_ability_hint_without_tag_card(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "想简单轻松地走走"},
    )
    body = first.json()
    choice = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "intent_dimensions",
                    "value": ["physical_ease"],
                    "label": ["体力轻松"],
                    "custom_text": None,
                }
            ],
        },
    )

    assert choice.status_code == 200
    items = choice.json()["confirmed_context"]["items"]
    ability = next(item for item in items if item["field"] == "ability_hint")
    assert ability["value"]
    # subjective-only → RAG done → next request is core, not a tag card
    next_fields = [
        q["field"] for q in (choice.json().get("choice_request") or {}).get("questions", [])
    ]
    assert "intent_dimensions" not in next_fields


def test_objective_dimension_yields_tag_card(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "想简单轻松地走走"},
    )
    body = first.json()
    choice = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "intent_dimensions",
                    "value": ["terrain"],
                    "label": ["路面好走"],
                    "custom_text": None,
                }
            ],
        },
    )

    assert choice.status_code == 200
    questions = choice.json()["choice_request"]["questions"]
    fields = [question["field"] for question in questions]
    assert "preference_tags" in fields
    tag_question = next(q for q in questions if q["field"] == "preference_tags")
    assert tag_question["multi_select"] is True
    labels = {option["label"] for option in tag_question["options"]}
    assert "公路/铺装路" in labels
    assert all(len(option["value"]) > 0 for option in tag_question["options"])


def test_tag_selection_writes_preference_tags(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "想简单轻松地走走"},
    )
    body = first.json()
    round_one = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "intent_dimensions",
                    "value": ["terrain"],
                    "label": ["路面好走"],
                    "custom_text": None,
                }
            ],
        },
    )
    round_one_body = round_one.json()
    round_two = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": round_one_body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "preference_tags",
                    "value": ["公路/铺装路", "石板平路"],
                    "label": ["公路/铺装路", "石板平路"],
                    "custom_text": None,
                }
            ],
        },
    )

    assert round_two.status_code == 200
    items = round_two.json()["confirmed_context"]["items"]
    preference = next(item for item in items if item["field"] == "preference_tags")
    assert "公路" in preference["value"]


def test_question_wording_under_100_chars_across_rag_rounds(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "想简单轻松地走走"},
    )
    for question in first.json()["choice_request"]["questions"]:
        assert len(question["question"]) <= 100


def test_safety_dimension_yields_avoid_tags_card(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "稳妥新手入门"},
    )
    body = first.json()
    dimension_question = next(
        q for q in body["choice_request"]["questions"] if q["field"] == "intent_dimensions"
    )
    assert "safety" in {opt["value"] for opt in dimension_question["options"]}

    choice = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "intent_dimensions",
                    "value": ["safety"],
                    "label": ["安全稳妥"],
                    "custom_text": None,
                }
            ],
        },
    )

    assert choice.status_code == 200
    questions = choice.json()["choice_request"]["questions"]
    fields = [question["field"] for question in questions]
    assert "avoid_tags" in fields
    avoid_question = next(q for q in questions if q["field"] == "avoid_tags")
    labels = {option["label"] for option in avoid_question["options"]}
    assert "无路标或路标数量稀少" in labels


def test_service_dimension_yields_service_preferences_card(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/api/trip-plans/messages",
        headers=auth_headers,
        json={"content": "亲子要补给"},
    )
    body = first.json()
    dimension_question = next(
        q for q in body["choice_request"]["questions"] if q["field"] == "intent_dimensions"
    )
    assert "service" in {opt["value"] for opt in dimension_question["options"]}

    choice = client.post(
        f"/api/trip-plans/{body['trip_plan_id']}/choice-results",
        headers=auth_headers,
        json={
            "choice_request_id": body["choice_request"]["choice_request_id"],
            "answers": [
                {
                    "field": "intent_dimensions",
                    "value": ["service"],
                    "label": ["服务补给"],
                    "custom_text": None,
                }
            ],
        },
    )

    assert choice.status_code == 200
    questions = choice.json()["choice_request"]["questions"]
    fields = [question["field"] for question in questions]
    assert "service_preferences" in fields
    service_question = next(q for q in questions if q["field"] == "service_preferences")
    labels = {option["label"] for option in service_question["options"]}
    assert "有小卖部" in labels
