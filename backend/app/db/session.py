"""数据库连接与会话管理。

提供 SQLAlchemy 引擎、ORM 基类和 FastAPI 依赖注入用的 get_db 生成器。
底部导入确保所有 ORM 模型在 engine 创建后注册到 Base.metadata。"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类，用于建表和查询。"""
    pass


settings = get_settings()
# SQLite 需要 check_same_thread=False 才能在多线程（FastAPI async）下正常工作
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：每个请求获取独立数据库会话，请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 必须在 engine 创建后导入，让所有模型的 Table 注册到 Base.metadata
# noqa 注释抑制 E402（导入不在顶部）和 F401（仅用于副作用）警告
from app.features.users import model as _user_model  # noqa: E402,F401
from app.features.routes import model as _route_model  # noqa: E402,F401
from app.features.trip_plans import model as _trip_plan_model  # noqa: E402,F401
