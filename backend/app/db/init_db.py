"""数据库建表工具。

调用 init_db() 会根据所有已注册的 ORM 模型自动创建缺失的表。
已存在的表不会被修改（不处理迁移）。"""

from __future__ import annotations

from app.db.session import Base, engine
from app.features.routes import model as _route_model  # noqa: F401
from app.features.trip_plans import model as _trip_plan_model  # noqa: F401
from app.features.users import model as _user_model  # noqa: F401


def init_db() -> None:
    """根据 ORM 模型定义创建所有数据库表（IF NOT EXISTS 语义）。"""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
