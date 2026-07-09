from __future__ import annotations

import json
from types import SimpleNamespace


def test_forward_geocode_returns_none_under_mock_amap(monkeypatch) -> None:
    from app.features.geo import forward as service

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=True,
            amap_web_service_key="test-key",
        ),
    )

    assert service.forward_geocode("成都") is None


def test_forward_geocode_returns_none_without_key(monkeypatch) -> None:
    from app.features.geo import forward as service

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=False,
            amap_web_service_key=None,
        ),
    )

    assert service.forward_geocode("成都") is None


def test_forward_geocode_parses_amap_response(monkeypatch) -> None:
    from app.features.geo import forward as service

    captured_url = ""

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "status": "1",
                    "info": "OK",
                    "geocodes": [{"location": "104.065735,30.659462"}],
                }
            ).encode("utf-8")

    def fake_urlopen(url, timeout):
        nonlocal captured_url
        captured_url = url
        return _FakeResponse()

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            use_mock_amap=False,
            amap_web_service_key="test-key",
        ),
    )
    monkeypatch.setattr(service.request, "urlopen", fake_urlopen)

    coord = service.forward_geocode("成都")

    assert coord is not None
    assert coord.lon == 104.065735
    assert coord.lat == 30.659462
    assert "key=test-key" in captured_url
    assert "address=" in captured_url
