from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory) -> TestClient:
    db_path = tmp_path / "test.db"
    avatar_dir = tmp_path / "avatars"
    route_dir = tmp_path / "routes"
    activity_dir = tmp_path / "activity_tracks"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["AVATAR_STORAGE_DIR"] = str(avatar_dir)
    os.environ["ROUTE_STORAGE_DIR"] = str(route_dir)
    os.environ["ACTIVITY_STORAGE_DIR"] = str(activity_dir)
    os.environ["USE_MOCK_AMAP"] = "true"

    from app.db.session import Base, engine
    from app.main import create_app

    Base.metadata.create_all(bind=engine)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def registered_user(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "outdoor_user",
            "password": "plain_password",
            "nickname": "山野用户",
        },
    )
    assert response.status_code == 201
    return response.json()["user"]


@pytest.fixture()
def auth_headers(client: TestClient, registered_user: dict[str, object]) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "outdoor_user", "password": "plain_password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
