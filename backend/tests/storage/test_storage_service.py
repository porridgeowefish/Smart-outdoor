from __future__ import annotations

from app.features.storage.service import StorageService


def test_cos_public_url_is_unsigned(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "cos")
    monkeypatch.setenv("COS_BUCKET", "smart-outdoor-test-1234567890")
    monkeypatch.setenv("COS_REGION", "ap-guangzhou")
    monkeypatch.delenv("COS_CDN_BASE_URL", raising=False)

    url = StorageService().public_url(
        "routes/user-id/track.geojson",
        provider="cos",
    )

    assert url == (
        "https://smart-outdoor-test-1234567890.cos.ap-guangzhou.myqcloud.com/"
        "routes/user-id/track.geojson"
    )
    assert "q-signature" not in url
    assert "q-sign-algorithm" not in url


def test_cos_upload_url_is_signed_put(monkeypatch) -> None:
    class FakeCosClient:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def get_presigned_url(self, **kwargs) -> str:
            self.calls.append(kwargs)
            return (
                "https://smart-outdoor-test-1234567890.cos.ap-guangzhou.myqcloud.com/"
                "routes/user-id/track.gpx?q-sign-algorithm=sha1&q-signature=fake"
            )

    monkeypatch.setenv("STORAGE_PROVIDER", "cos")
    monkeypatch.setenv("COS_BUCKET", "smart-outdoor-test-1234567890")
    monkeypatch.setenv("COS_REGION", "ap-guangzhou")
    fake_client = FakeCosClient()
    service = StorageService()
    monkeypatch.setattr(service, "_cos_client", lambda: fake_client)

    url = service.upload_url("routes/user-id/track.gpx", provider="cos")

    assert "q-signature=fake" in url
    assert fake_client.calls == [
        {
            "Method": "PUT",
            "Bucket": "smart-outdoor-test-1234567890",
            "Key": "routes/user-id/track.gpx",
            "Expired": 15 * 60,
        }
    ]
