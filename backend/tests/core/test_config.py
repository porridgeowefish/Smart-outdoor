from __future__ import annotations


def test_get_settings_loads_env_file(monkeypatch, tmp_path) -> None:
    from app.core.config import get_settings

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "USE_MOCK_AMAP=false",
                "AMAP_WEB_SERVICE_KEY=test-key",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SMART_OUTDOOR_ENV_FILE", str(env_file))
    monkeypatch.delenv("USE_MOCK_AMAP", raising=False)
    monkeypatch.delenv("AMAP_WEB_SERVICE_KEY", raising=False)

    settings = get_settings()

    assert settings.use_mock_amap is False
    assert settings.amap_web_service_key == "test-key"
