from __future__ import annotations

import os

import pytest


@pytest.fixture()
def db_session(tmp_path: pytest.TempPathFactory):
    db_path = tmp_path / "service.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"

    from app.db.session import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user_hashes_password(db_session) -> None:
    from app.features.auth.schemas import RegisterRequest
    from app.features.auth.service import create_user
    from app.features.users.model import User

    user = create_user(
        db_session,
        RegisterRequest(
            username="outdoor_user",
            password="plain_password",
            nickname="山野用户",
        ),
    )
    saved = db_session.get(User, user.id)

    assert saved is not None
    assert saved.password_hash != "plain_password"
    assert saved.password_hash


def test_authenticate_user_accepts_username(db_session) -> None:
    from app.features.auth.schemas import RegisterRequest
    from app.features.auth.service import authenticate_user, create_user

    create_user(
        db_session,
        RegisterRequest(
            username="outdoor_user",
            password="plain_password",
            nickname="山野用户",
        ),
    )

    assert authenticate_user(db_session, "outdoor_user", "plain_password") is not None


def test_authenticate_user_rejects_wrong_password(db_session) -> None:
    from app.features.auth.schemas import RegisterRequest
    from app.features.auth.service import authenticate_user, create_user

    create_user(
        db_session,
        RegisterRequest(
            username="outdoor_user",
            password="plain_password",
            nickname="山野用户",
        ),
    )

    assert authenticate_user(db_session, "outdoor_user", "wrong_password") is None


def test_create_user_rejects_duplicate_identity(db_session) -> None:
    from app.features.auth.schemas import RegisterRequest
    from app.features.auth.service import DuplicateUserError, create_user

    create_user(
        db_session,
        RegisterRequest(
            username="outdoor_user",
            password="plain_password",
            nickname="山野用户",
        ),
    )

    with pytest.raises(DuplicateUserError):
        create_user(
            db_session,
            RegisterRequest(
                username="outdoor_user",
                password="plain_password",
                nickname="另一个用户",
            ),
        )
