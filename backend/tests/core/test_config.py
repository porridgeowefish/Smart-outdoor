from __future__ import annotations


def test_get_settings_loads_env_file(monkeypatch, tmp_path) -> None:
    from app.core.config import get_settings

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "USE_MOCK_AMAP=false",
                "USE_MOCK_SEARCH=false",
                "USE_MOCK_LLM=false",
                "AMAP_WEB_SERVICE_KEY=test-key",
                "TAVILY_API_KEY=tavily-test-key",
                "OPENAI_API_KEY=openai-test-key",
                "OPENAI_API_KEY=openai-latest-key",
                "OPENAI_MODEL=test-model",
                "OPENAI_BASE_URL=https://example.com/v1",
                "LLM_TIMEOUT_SECONDS=3.5",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SMART_OUTDOOR_ENV_FILE", str(env_file))
    monkeypatch.delenv("USE_MOCK_AMAP", raising=False)
    monkeypatch.delenv("USE_MOCK_SEARCH", raising=False)
    monkeypatch.delenv("USE_MOCK_LLM", raising=False)
    monkeypatch.delenv("AMAP_WEB_SERVICE_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)

    settings = get_settings()

    assert settings.use_mock_amap is False
    assert settings.use_mock_search is False
    assert settings.use_mock_llm is False
    assert settings.amap_web_service_key == "test-key"
    assert settings.tavily_api_key == "tavily-test-key"
    assert settings.openai_api_key == "openai-latest-key"
    assert settings.openai_model == "test-model"
    assert settings.openai_base_url == "https://example.com/v1"
    assert settings.llm_timeout_seconds == 3.5
