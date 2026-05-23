"""数据库建表工具。

调用 init_db() 会根据所有已注册的 ORM 模型自动创建缺失的表。
已存在的表不会被修改（不处理迁移）。"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import Base, engine
from app.features.routes import model as _route_model  # noqa: F401
from app.features.trip_plans import model as _trip_plan_model  # noqa: F401
from app.features.users import model as _user_model  # noqa: F401


def init_db() -> None:
    """根据 ORM 模型定义创建所有数据库表（IF NOT EXISTS 语义）。"""
    Base.metadata.create_all(bind=engine)
    _ensure_iteration_07_columns()
    _ensure_iteration_08_columns()


def _ensure_iteration_07_columns() -> None:
    """Best-effort additive schema sync for existing dev databases.

    The project does not have a migration framework yet. This keeps local
    PostgreSQL/SQLite databases usable while preserving create_all for tests.
    """
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return
    columns = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in ("users", "route_assets", "route_files", "route_analysis_snapshots")
        if inspector.has_table(table)
    }
    additions = {
        "users": {
            "avatar_storage_provider": "VARCHAR(32)",
            "avatar_storage_key": "VARCHAR(500)",
            "avatar_variants": _json_type(),
            "avatar_original_filename": "VARCHAR(255)",
            "avatar_processing_status": "VARCHAR(32)",
        },
        "route_assets": {
            "cover_storage_provider": "VARCHAR(32)",
            "cover_storage_key": "VARCHAR(500)",
            "cover_image_variants": _json_type(),
            "cover_original_filename": "VARCHAR(255)",
            "cover_processing_status": "VARCHAR(32)",
        },
        "route_files": {
            "storage_provider": "VARCHAR(32)",
            "storage_key": "VARCHAR(500)",
            "content_type": "VARCHAR(120)",
            "original_filename": "VARCHAR(255)",
        },
        "route_analysis_snapshots": {
            "track_preview_geojson": _json_type(),
            "track_preview_point_count": "INTEGER",
            "track_geojson_storage_provider": "VARCHAR(32)",
            "track_geojson_storage_key": "VARCHAR(500)",
            "track_geojson_url": "VARCHAR(500)",
            "track_geojson_point_count": "INTEGER",
            "track_geojson_size_bytes": "INTEGER",
        },
    }
    with engine.begin() as connection:
        for table, table_additions in additions.items():
            existing = columns.get(table, set())
            for name, column_type in table_additions.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {column_type}"))


def _ensure_iteration_08_columns() -> None:
    """Best-effort additive schema sync for choice-based TripPlan messages."""
    inspector = inspect(engine)
    if not inspector.has_table("trip_plan_messages"):
        return
    existing = {column["name"] for column in inspector.get_columns("trip_plan_messages")}
    additions = {
        "content_type": "VARCHAR(32) DEFAULT 'text'",
        "payload": _json_type(),
    }
    with engine.begin() as connection:
        for name, column_type in additions.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE trip_plan_messages ADD COLUMN {name} {column_type}")
                )


def _json_type() -> str:
    return "JSONB" if engine.dialect.name == "postgresql" else "JSON"


if __name__ == "__main__":
    init_db()
