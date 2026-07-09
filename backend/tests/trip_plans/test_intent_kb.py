from __future__ import annotations

from app.features.llm.mock import MockLLMProvider
from app.features.trip_plans.intent_kb import (
    DIMENSIONS,
    INTENTS,
    IntentKB,
    merge_dimensions,
)


def _kb() -> IntentKB:
    return IntentKB(MockLLMProvider())


def test_intent_kb_recall_returns_intent_for_exact_phrase() -> None:
    hits = _kb().recall("简单")

    assert hits
    assert hits[0].intent == "easy_simple"


def test_intent_kb_recall_labels_subjective_and_objective_dimensions() -> None:
    hits = _kb().recall("简单")
    dims = merge_dimensions(hits)

    keys = {d["key"] for d in dims}
    assert "physical_ease" in keys
    assert "terrain" in keys
    assert DIMENSIONS["physical_ease"]["type"] == "subjective"
    assert DIMENSIONS["terrain"]["type"] == "objective"


def test_intent_kb_recall_objective_dimension_has_tag_source() -> None:
    dims = merge_dimensions(_kb().recall("简单"))
    terrain = next(d for d in dims if d["key"] == "terrain")

    assert terrain["tag_source"]
    assert terrain["write_field"] == "preference_tags"


def test_intent_kb_merge_caps_at_four_dimensions() -> None:
    # family intent carries 3 dims; combined with others can exceed 4.
    hits = _kb().recall("亲子")
    dims = merge_dimensions(hits, max_dimensions=4)

    assert len(dims) <= 4


def test_intent_kb_recall_degrades_on_empty_query() -> None:
    assert _kb().recall("") == []


def test_intent_kb_falls_back_to_substring_when_embedding_fails() -> None:
    class _BrokenProvider:
        provider_name = "broken"

        def embed_texts(self, texts):
            raise RuntimeError("boom")

    kb = IntentKB(_BrokenProvider())

    assert kb.available is False
    # embedding down → substring layer still matches an exact phrase
    hits = kb.recall("简单")
    assert hits and hits[0].intent == "easy_simple"


def test_intent_kb_below_threshold_intent_dropped() -> None:
    # A phrase that matches nothing in the KB → no hit (sparse mock → ~0 cosine).
    hits = _kb().recall("zzz不存在的查询xxx")

    assert hits == []


def test_intent_kb_recall_safety_steady_includes_safety_dimension() -> None:
    dims = merge_dimensions(_kb().recall("稳妥"))

    safety = next(d for d in dims if d["key"] == "safety")
    assert safety["write_field"] == "avoid_tags"
    assert "无路标或路标数量稀少" in safety["tag_source"]


def test_intent_kb_recall_supply_service_includes_service_dimension() -> None:
    dims = merge_dimensions(_kb().recall("补给"))

    service = next(d for d in dims if d["key"] == "service")
    assert service["write_field"] == "service_preferences"
    assert "有小卖部" in service["tag_source"]


def test_intent_kb_every_intent_has_description_for_richer_embedding() -> None:
    assert all(intent.description for intent in INTENTS)
