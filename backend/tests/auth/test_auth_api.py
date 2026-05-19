from __future__ import annotations

from fastapi.testclient import TestClient

from tests.routes.upload_helpers import image_asset


def test_register_success_returns_public_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "outdoor_user",
            "password": "plain_password",
            "nickname": "山野用户",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "user": {
            "id": response.json()["user"]["id"],
            "username": "outdoor_user",
            "nickname": "山野用户",
            "avatar_url": None,
            "role": "user",
        }
    }
    assert "password" not in response.text
    assert "password_hash" not in response.text


def test_register_rejects_duplicate_username(
    client: TestClient, registered_user: dict[str, object]
) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "outdoor_user",
            "password": "plain_password",
            "nickname": "另一个用户",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "USER_ALREADY_EXISTS",
        "message": "用户名已被使用",
    }


def test_register_requires_username(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "password": "plain_password",
            "nickname": "山野用户",
        },
    )

    assert response.status_code == 422


def test_register_allows_nickname_to_default_to_username(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "outdoor_user",
            "password": "plain_password",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["nickname"] == "outdoor_user"


def test_login_success_returns_bearer_token(
    client: TestClient, registered_user: dict[str, object]
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "outdoor_user", "password": "plain_password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "outdoor_user"
    assert data["user"]["nickname"] == "山野用户"


def test_login_rejects_wrong_password(
    client: TestClient, registered_user: dict[str, object]
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "outdoor_user", "password": "wrong_password"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_CREDENTIALS",
        "message": "账号或密码错误",
    }


def test_get_me_requires_authorization(client: TestClient) -> None:
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_get_me_returns_current_user(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "outdoor_user"
    assert data["nickname"] == "山野用户"
    assert data["avatar_url"] is None
    assert data["role"] == "user"
    assert data["status"] == "active"
    assert data["created_at"]


def test_patch_me_updates_only_profile_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/me",
        headers=auth_headers,
            json={"nickname": "雪山徒步者"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "雪山徒步者"
    assert data["role"] == "user"
    assert data["status"] == "active"


def test_patch_me_rejects_unallowed_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/me",
        headers=auth_headers,
        json={"nickname": "雪山徒步者", "role": "admin"},
    )

    assert response.status_code == 422


def test_patch_me_updates_avatar_metadata(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    avatar = image_asset(
        client,
        auth_headers,
        asset_type="avatar",
        original_filename="avatar.jpg",
        variants={
            "display": (b"display-webp", 512, 512),
            "thumbnail": (b"thumb-webp", 128, 128),
        },
    )
    response = client.patch(
        "/api/me",
        headers=auth_headers,
        json={"avatar": avatar},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"].startswith("/static/assets/")
    assert data["avatar_storage_key"] == avatar["variants"]["display"]["storage_key"]
    assert data["avatar_variants"]["thumbnail"]["url"].endswith(".webp")

    me_response = client.get("/api/me", headers=auth_headers)
    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"] == data["avatar_url"]

    static_response = client.get(data["avatar_url"])
    assert static_response.status_code == 200
    assert static_response.content == b"display-webp"


def test_upload_credentials_requires_authorization(client: TestClient) -> None:
    response = client.post("/api/storage/upload-credentials", json={})

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_patch_me_rejects_unowned_avatar_metadata(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/me",
        headers=auth_headers,
        json={
            "avatar": {
                "storage_provider": "local",
                "storage_key": "users/other/avatar/display.webp",
                "url": "/static/assets/users/other/avatar/display.webp",
                "original_filename": "avatar.webp",
                "processing_status": "ready",
                "variants": {
                    "display": {
                        "storage_key": "users/other/avatar/display.webp",
                        "url": "/static/assets/users/other/avatar/display.webp",
                        "width": 512,
                        "height": 512,
                        "content_type": "image/webp",
                        "size_bytes": 10,
                    }
                },
            }
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_STORAGE_OBJECT"


def test_openapi_exposes_auth_and_me_contracts(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/me" in paths
    assert "/api/storage/upload-credentials" in paths
