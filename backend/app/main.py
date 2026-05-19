"""FastAPI 应用入口。

负责创建应用实例、注册路由、挂载静态文件目录，
并通过 lifespan 在启动时自动建表。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db.init_db import init_db
from app.features.auth.router import router as auth_router
from app.features.routes.router import router as routes_router
from app.features.storage.router import router as storage_router
from app.features.trip_plans.router import router as trip_plans_router
from app.features.users.deps import AuthError, unauthorized_response
from app.features.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用启动时根据 ORM 模型自动创建所有数据库表。"""
    init_db()
    yield


def create_app() -> FastAPI:
    """构建并返回完整的 FastAPI 应用实例。

    注册顺序：全局异常处理 → 静态文件挂载 → 业务路由（auth/users/routes）。
    """
    app = FastAPI(title="Smart Outdoor API", lifespan=lifespan)
    settings = get_settings()

    # 将 AuthError 统一转为 401 JSON 响应，避免抛出 500
    @app.exception_handler(AuthError)
    def handle_auth_error(request, exc):
        return unauthorized_response()

    # 静态文件：头像和线路附件分别挂载到不同路径
    app.mount(
        "/static/avatars",
        StaticFiles(directory=settings.avatar_storage_dir, check_dir=False),
        name="avatars",
    )
    app.mount(
        "/static/routes",
        StaticFiles(directory=settings.route_storage_dir, check_dir=False),
        name="routes",
    )
    app.mount(
        "/static/activity-tracks",
        StaticFiles(directory=settings.activity_storage_dir, check_dir=False),
        name="activity-tracks",
    )
    app.mount(
        "/static/assets",
        StaticFiles(directory=settings.asset_storage_dir, check_dir=False),
        name="assets",
    )
    app.include_router(auth_router, prefix="/api")
    app.include_router(storage_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(routes_router, prefix="/api")
    app.include_router(trip_plans_router, prefix="/api")
    return app


app = create_app()
