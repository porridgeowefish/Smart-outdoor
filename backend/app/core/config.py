from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    jwt_access_token_expire_minutes: int
    avatar_storage_dir: str
    route_storage_dir: str
    activity_storage_dir: str
    asset_storage_dir: str
    storage_provider: str
    storage_public_base_url: str
    cos_secret_id: str | None
    cos_secret_key: str | None
    cos_token: str | None
    cos_bucket: str | None
    cos_region: str | None
    cos_cdn_base_url: str | None
    use_mock_amap: bool
    use_mock_weather: bool
    use_mock_search: bool
    use_mock_llm: bool
    amap_web_service_key: str | None
    amap_reverse_geocode_url: str
    qweather_api_key: str | None
    weather_developer_host: str
    tavily_api_key: str | None
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str
    llm_timeout_seconds: float


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://smart_outdoor:smart_outdoor_dev_password"
            "@127.0.0.1:5432/smart_outdoor",
        ),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-change-me"),
        jwt_access_token_expire_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
        avatar_storage_dir=os.getenv("AVATAR_STORAGE_DIR", "storage/avatars"),
        route_storage_dir=os.getenv("ROUTE_STORAGE_DIR", "storage/routes"),
        activity_storage_dir=os.getenv(
            "ACTIVITY_STORAGE_DIR", "storage/activity_tracks"
        ),
        asset_storage_dir=os.getenv("ASSET_STORAGE_DIR", "storage/assets"),
        storage_provider=os.getenv("STORAGE_PROVIDER", "local").lower(),
        storage_public_base_url=os.getenv(
            "STORAGE_PUBLIC_BASE_URL", "/static/assets"
        ).rstrip("/"),
        cos_secret_id=os.getenv("COS_SECRET_ID"),
        cos_secret_key=os.getenv("COS_SECRET_KEY"),
        cos_token=os.getenv("COS_TOKEN"),
        cos_bucket=os.getenv("COS_BUCKET"),
        cos_region=os.getenv("COS_REGION"),
        cos_cdn_base_url=os.getenv("COS_CDN_BASE_URL"),
        use_mock_amap=os.getenv("USE_MOCK_AMAP", "true").lower() == "true",
        use_mock_weather=os.getenv("USE_MOCK_WEATHER", "true").lower() == "true",
        use_mock_search=os.getenv("USE_MOCK_SEARCH", "true").lower() == "true",
        use_mock_llm=os.getenv("USE_MOCK_LLM", "true").lower() == "true",
        amap_web_service_key=os.getenv("AMAP_WEB_SERVICE_KEY"),
        amap_reverse_geocode_url=os.getenv(
            "AMAP_REVERSE_GEOCODE_URL",
            "https://restapi.amap.com/v3/geocode/regeo",
        ),
        qweather_api_key=os.getenv("QWEATHER_API_KEY"),
        weather_developer_host=os.getenv(
            "WEATHER_DEVELOPER_HOST",
            "devapi.qweather.com",
        ),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
    )


def _load_dotenv() -> None:
    env_path = os.getenv("SMART_OUTDOOR_ENV_FILE")
    backend_root = Path(__file__).resolve().parents[2]
    if env_path:
        paths = [_resolve_config_path(raw_path, backend_root) for raw_path in env_path.split(os.pathsep)]
    else:
        paths = [
            backend_root / ".env",
            backend_root / "config" / "app.local.env",
        ]

    for path in paths:
        if not path.exists():
            continue
        values: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip().lstrip("\ufeff")
            value = value.strip().strip('"').strip("'")
            if name:
                values[name] = value
        for name, value in values.items():
            if name not in os.environ:
                os.environ[name] = value


def _resolve_config_path(raw_path: str, backend_root: Path) -> Path:
    path = Path(raw_path.strip())
    if path.is_absolute():
        return path
    return backend_root / path
