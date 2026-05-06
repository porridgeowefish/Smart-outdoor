from __future__ import annotations

from fastapi.testclient import TestClient


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
        json={
            "nickname": "雪山徒步者",
            "avatar_url": "https://cdn.example.com/avatar.jpg",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "雪山徒步者"
    assert data["avatar_url"] == "https://cdn.example.com/avatar.jpg"
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


def test_upload_avatar_updates_current_user(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/me/avatar",
        headers=auth_headers,
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar-bytes", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"].startswith("/static/avatars/")
    assert data["avatar_url"].endswith(".png")

    me_response = client.get("/api/me", headers=auth_headers)
    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"] == data["avatar_url"]

    static_response = client.get(data["avatar_url"])
    assert static_response.status_code == 200
    assert static_response.content == b"\x89PNG\r\n\x1a\navatar-bytes"


def test_upload_avatar_requires_authorization(client: TestClient) -> None:
    response = client.post(
        "/api/me/avatar",
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar-bytes", "image/png")},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_upload_avatar_rejects_non_image_file(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/me/avatar",
        headers=auth_headers,
        files={"file": ("avatar.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_AVATAR_FILE",
        "message": "仅支持 JPG、PNG、WebP 或 GIF 图片",
    }


def test_openapi_exposes_auth_and_me_contracts(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/me" in paths
    assert "/api/me/avatar" in paths
