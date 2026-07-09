from __future__ import annotations

from types import SimpleNamespace

from app.features.llm.mock import MockLLMProvider
from app.features.llm.openai_provider import OpenAILLMProvider


def test_mock_embed_texts_is_deterministic_and_shaped() -> None:
    provider = MockLLMProvider()

    first = provider.embed_texts(["简单", "轻松"])
    second = provider.embed_texts(["简单", "轻松"])

    assert first == second
    assert len(first) == 2
    assert all(len(vector) > 0 for vector in first)
    assert first[0] != first[1]


def test_mock_embed_texts_empty_input_returns_empty() -> None:
    assert MockLLMProvider().embed_texts([]) == []


def test_mock_embed_texts_same_text_same_vector() -> None:
    provider = MockLLMProvider()
    assert provider.embed_texts(["简单"])[0] == provider.embed_texts(["简单"])[0]


def test_openai_embed_texts_parses_response() -> None:
    class _FakeEmbeddings:
        def create(self, *, model, input):
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[0.1, 0.2], index=0),
                    SimpleNamespace(embedding=[0.3, 0.4], index=1),
                ]
            )

    class _FakeClient:
        def __init__(self):
            self.embeddings = _FakeEmbeddings()

    provider = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://example.com/v1",
        embedding_model="emb-model",
        client=_FakeClient(),
    )

    assert provider.embed_texts(["a", "b"]) == [[0.1, 0.2], [0.3, 0.4]]


def test_openai_embed_texts_falls_back_on_error() -> None:
    class _BrokenEmbeddings:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class _BrokenClient:
        def __init__(self):
            self.embeddings = _BrokenEmbeddings()

    provider = OpenAILLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://example.com/v1",
        client=_BrokenClient(),
    )

    result = provider.embed_texts(["a"])

    assert len(result) == 1
    assert len(result[0]) > 0
