from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Dimension catalog.
# subjective → writes ability_hint{level}, no tag card.
# objective  → tag card (options from tag_source) → write_field (an array field).
DIMENSIONS: dict[str, dict[str, Any]] = {
    "physical_ease": {
        "type": "subjective",
        "label": "体力轻松",
        "ability_level": "beginner",
    },
    "stimulating": {
        "type": "subjective",
        "label": "刺激有挑战",
        "ability_level": "strong",
    },
    "terrain": {
        "type": "objective",
        "label": "路面好走",
        "header": "路面",
        "question": "路面你更想要哪种？",
        "tag_source": ["公路/铺装路", "石板平路", "土路/机耕路", "台阶路/阶梯路"],
        "write_field": "preference_tags",
    },
    "scenery": {
        "type": "objective",
        "label": "看风景",
        "header": "风景",
        "question": "更想看哪种风景？",
        "tag_source": ["云海", "日出", "雪山", "森林", "溪流", "瀑布", "湖泊", "星空"],
        "write_field": "scenery_preferences",
    },
    "safety": {
        "type": "objective",
        "label": "安全稳妥",
        "header": "安全/导航",
        "question": "安全或导航上想避开哪些？",
        "tag_source": ["无路标或路标数量稀少", "无下撤点"],
        "write_field": "avoid_tags",
    },
    "service": {
        "type": "objective",
        "label": "服务补给",
        "header": "服务/补给",
        "question": "服务或补给想要哪些？",
        "tag_source": ["有小卖部", "有餐饮点", "有饮用水", "卫生间", "医疗点"],
        "write_field": "service_preferences",
    },
}


@dataclass(frozen=True)
class Intent:
    name: str
    phrases: tuple[str, ...]
    dimensions: tuple[str, ...]
    description: str


# Intent KB (local, in-repo, human-editable; tag values reference TAG_TAXONOMY).
# `description` is embedded alongside phrases so real embeddings get richer
# semantic signal; substring recall still keys off the short phrases.
INTENTS: list[Intent] = [
    Intent(
        "easy_simple",
        ("简单", "轻松", "不累", "休闲"),
        ("physical_ease", "terrain"),
        "希望线路简单轻松、不累，适合休闲放松，路面好走、体力要求低。",
    ),
    Intent(
        "stimulating_challenge",
        ("刺激", "挑战", "有难度", "硬核"),
        ("stimulating", "terrain"),
        "想要有挑战、刺激、有难度的硬核线路，体力强度高。",
    ),
    Intent(
        "scenery_photo",
        ("拍照", "出片", "风景", "好看", "景色"),
        ("scenery",),
        "主要为了风景好看、拍照出片，想看好看的景色。",
    ),
    Intent(
        "snow_play",
        ("看雪", "雪山", "雪景", "冰川"),
        ("scenery",),
        "想看雪、雪山、雪景、冰川等冬季风光。",
    ),
    Intent(
        "family",
        ("亲子", "带娃", "家庭", "小朋友"),
        ("physical_ease", "terrain", "scenery"),
        "亲子家庭出行，带小朋友，轻松安全、风景好。",
    ),
    Intent(
        "night_hike",
        ("夜爬", "夜行", "星空", "日出"),
        ("scenery",),
        "夜爬或夜行，想看星空、日出。",
    ),
    Intent(
        "safety_steady",
        ("稳妥", "安全", "新手", "入门"),
        ("physical_ease", "terrain", "safety"),
        "稳妥安全的新手入门线路，路面好走、有路标、风险低。",
    ),
    Intent(
        "supply_service",
        ("补给", "卫生间", "水源", "小卖部", "吃饭", "医疗"),
        ("service",),
        "关注补给和服务设施，需要小卖部、餐饮、水源、卫生间或医疗点。",
    ),
]


@dataclass(frozen=True)
class RecallHit:
    intent: str
    confidence: float
    dimensions: tuple[str, ...]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class IntentKB:
    """In-memory intent knowledge base with embedding-based recall.

    Indexes each intent's trigger phrases AND its description. recall() scores
    an intent by max over (phrases + description) of max(embedding cosine,
    substring match). Substring makes recall deterministic offline and robust
    to a failed/degraded embedding; real embeddings get semantic signal from
    the descriptions. If embedding is unavailable the index is empty but
    substring recall (off INTENTS) still works.
    """

    def __init__(self, provider: Any, *, threshold: float = 0.35) -> None:
        self._provider = provider
        self.threshold = threshold
        self._index: dict[str, list[tuple[str, list[float]]]] = {}
        texts: list[str] = []
        owners: list[str] = []
        for intent in INTENTS:
            for phrase in intent.phrases:
                texts.append(phrase)
                owners.append(intent.name)
            texts.append(intent.description)
            owners.append(intent.name)
        try:
            vectors = provider.embed_texts(texts)
        except Exception:
            vectors = []
        if vectors and len(vectors) == len(texts):
            for text, intent_name, vector in zip(texts, owners, vectors):
                self._index.setdefault(intent_name, []).append((text, vector))

    @property
    def available(self) -> bool:
        return bool(self._index)

    def recall(self, query: str) -> list[RecallHit]:
        if not query:
            return []
        query_vec: list[float] | None = None
        if self._index:
            try:
                query_vectors = self._provider.embed_texts([query])
            except Exception:
                query_vectors = []
            if query_vectors:
                query_vec = query_vectors[0]
        best: dict[str, float] = {}
        for intent in INTENTS:
            intent_best = 0.0
            # substring layer: always available (off INTENTS), deterministic.
            for text in (*intent.phrases, intent.description):
                if text in query:
                    intent_best = max(intent_best, 1.0)
            # embedding layer: cosine over indexed phrase + description vectors.
            if query_vec is not None:
                for _text, vector in self._index.get(intent.name, []):
                    intent_best = max(intent_best, _cosine(query_vec, vector))
            if intent_best >= self.threshold:
                best[intent.name] = intent_best
        ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)
        hits: list[RecallHit] = []
        for intent_name, score in ranked:
            dims = next(
                (intent.dimensions for intent in INTENTS if intent.name == intent_name),
                (),
            )
            hits.append(RecallHit(intent=intent_name, confidence=score, dimensions=dims))
        return hits


def merge_dimensions(hits: list[RecallHit], *, max_dimensions: int = 4) -> list[dict[str, Any]]:
    """Dedup dimensions across hits (confidence order), cap at max_dimensions.

    Pure rule-layer merge (no LLM): collects dimension keys in hit order,
    attaches their DIMENSIONS meta. Returns [] if no dims.
    """
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for hit in hits:
        for dim_key in hit.dimensions:
            if dim_key in seen:
                continue
            meta = DIMENSIONS.get(dim_key)
            if meta is None:
                continue
            seen.add(dim_key)
            result.append({"key": dim_key, **meta})
            if len(result) >= max_dimensions:
                return result
    return result
