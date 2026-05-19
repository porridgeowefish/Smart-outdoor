from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.features.routes.model import RouteAnalysisSnapshot, RouteAsset, RouteFile
from app.features.routes.service import build_high_fidelity_preview
from app.features.storage.service import StorageService, UnsupportedStorageProviderError
from app.features.users.model import User


@dataclass(frozen=True)
class SourceObject:
    content: bytes
    content_type: str
    filename: str


@dataclass
class MigrationStats:
    planned: int = 0
    uploaded: int = 0
    skipped: int = 0
    failed: int = 0

    def add(self, other: "MigrationStats") -> None:
        self.planned += other.planned
        self.uploaded += other.uploaded
        self.skipped += other.skipped
        self.failed += other.failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate existing database asset references into Tencent COS."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload objects and update database. Without this flag the script only prints a dry run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-upload rows that already have COS storage metadata.",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Base URL used to download legacy /static/... URLs when files are not available on disk.",
    )
    parser.add_argument(
        "--skip-route-files",
        action="store_true",
        help="Do not migrate route raw files.",
    )
    parser.add_argument(
        "--skip-derived-tracks",
        action="store_true",
        help="Do not migrate route derived GeoJSON snapshots.",
    )
    parser.add_argument(
        "--skip-avatars",
        action="store_true",
        help="Do not migrate legacy user avatars.",
    )
    parser.add_argument(
        "--skip-covers",
        action="store_true",
        help="Do not migrate legacy route covers.",
    )
    args = parser.parse_args()

    settings = get_settings()
    storage = StorageService()
    if args.apply and storage.provider != "cos":
        print("Refusing to apply: STORAGE_PROVIDER must be cos.", file=sys.stderr)
        return 2

    print("Mode:", "APPLY" if args.apply else "DRY RUN")
    print("Database:", _safe_database_label(settings.database_url))
    print("Storage provider:", storage.provider)
    if storage.provider == "cos":
        print("COS bucket:", settings.cos_bucket or "(missing)")
        print("COS region:", settings.cos_region or "(missing)")

    db = SessionLocal()
    total = MigrationStats()
    try:
        if not args.skip_route_files:
            total.add(migrate_route_files(db, storage, settings, args))
        if not args.skip_derived_tracks:
            total.add(migrate_derived_tracks(db, storage, args))
        if not args.skip_avatars:
            total.add(migrate_avatars(db, storage, settings, args))
        if not args.skip_covers:
            total.add(migrate_covers(db, storage, settings, args))
    finally:
        db.close()

    print(
        "Summary:",
        f"planned={total.planned}",
        f"uploaded={total.uploaded}",
        f"skipped={total.skipped}",
        f"failed={total.failed}",
    )
    return 1 if total.failed else 0


def migrate_route_files(db, storage: StorageService, settings, args) -> MigrationStats:
    stats = MigrationStats()
    rows = db.query(RouteFile).order_by(RouteFile.created_at.asc()).all()
    print(f"\nRoute raw files: {len(rows)} rows")
    for row in rows:
        if _already_cos(row.storage_provider) and not args.force:
            stats.skipped += 1
            continue
        stats.planned += 1
        key = _route_raw_key(row)
        label = f"route_file:{row.id}"
        try:
            source = _read_source_object(
                row.file_url,
                settings=settings,
                base_url=args.base_url,
                fallback_filename=row.original_filename or f"{row.id}.{row.file_type}",
                fallback_content_type=row.content_type,
            )
        except Exception as exc:
            stats.failed += 1
            print(f"  FAIL {label}: cannot read source {row.file_url!r}: {exc}")
            continue
        print(f"  {'UPLOAD' if args.apply else 'PLAN'} {label} -> {key}")
        if not args.apply:
            continue
        try:
            stored = storage.put_bytes(
                key=key,
                content=source.content,
                content_type=source.content_type,
                provider="cos",
            )
        except UnsupportedStorageProviderError as exc:
            stats.failed += 1
            print(f"  FAIL {label}: COS provider is not configured: {exc}")
            continue
        row.storage_provider = stored.provider
        row.storage_key = stored.key
        row.file_url = stored.url
        row.content_type = source.content_type
        row.original_filename = row.original_filename or source.filename
        row.file_size_bytes = len(source.content)
        row.checksum = hashlib.sha256(source.content).hexdigest()
        db.add(row)
        db.commit()
        stats.uploaded += 1
    return stats


def migrate_derived_tracks(db, storage: StorageService, args) -> MigrationStats:
    stats = MigrationStats()
    rows = (
        db.query(RouteAnalysisSnapshot, RouteAsset)
        .join(RouteAsset, RouteAsset.id == RouteAnalysisSnapshot.route_asset_id)
        .order_by(RouteAnalysisSnapshot.created_at.asc())
        .all()
    )
    print(f"\nDerived track GeoJSON: {len(rows)} rows")
    for snapshot, route in rows:
        if _already_cos(snapshot.track_geojson_storage_provider) and not args.force:
            stats.skipped += 1
            continue
        if not snapshot.track_geojson:
            stats.skipped += 1
            continue
        stats.planned += 1
        key = f"users/{route.created_by_user_id}/routes/{route.id}/derived/full.geojson"
        label = f"analysis:{snapshot.id}"
        content = json.dumps(snapshot.track_geojson, ensure_ascii=False).encode("utf-8")
        print(f"  {'UPLOAD' if args.apply else 'PLAN'} {label} -> {key}")
        if not args.apply:
            continue
        try:
            stored = storage.put_bytes(
                key=key,
                content=content,
                content_type="application/geo+json",
                provider="cos",
            )
        except UnsupportedStorageProviderError as exc:
            stats.failed += 1
            print(f"  FAIL {label}: COS provider is not configured: {exc}")
            continue
        preview = snapshot.track_preview_geojson or build_high_fidelity_preview(snapshot.track_geojson)
        snapshot.track_preview_geojson = preview
        snapshot.track_preview_point_count = len(preview.get("coordinates") or [])
        snapshot.track_geojson_storage_provider = stored.provider
        snapshot.track_geojson_storage_key = stored.key
        snapshot.track_geojson_url = stored.url
        snapshot.track_geojson_point_count = len(snapshot.track_geojson.get("coordinates") or [])
        snapshot.track_geojson_size_bytes = stored.size_bytes
        db.add(snapshot)
        db.commit()
        stats.uploaded += 1
    return stats


def migrate_avatars(db, storage: StorageService, settings, args) -> MigrationStats:
    stats = MigrationStats()
    rows = db.query(User).filter(User.avatar_url.is_not(None)).order_by(User.created_at.asc()).all()
    print(f"\nLegacy avatars: {len(rows)} rows")
    for user in rows:
        if _already_cos(user.avatar_storage_provider) and not args.force:
            stats.skipped += 1
            continue
        stats.planned += 1
        label = f"user_avatar:{user.id}"
        try:
            source = _read_source_object(
                user.avatar_url,
                settings=settings,
                base_url=args.base_url,
                fallback_filename=user.avatar_original_filename or f"{user.id}.jpg",
                fallback_content_type=None,
            )
        except Exception as exc:
            stats.failed += 1
            print(f"  FAIL {label}: cannot read source {user.avatar_url!r}: {exc}")
            continue
        extension = _extension_for(source.filename, source.content_type)
        key = f"users/{user.id}/avatar/display-migrated{extension}"
        print(f"  {'UPLOAD' if args.apply else 'PLAN'} {label} -> {key}")
        if not args.apply:
            continue
        try:
            stored = storage.put_bytes(
                key=key,
                content=source.content,
                content_type=source.content_type,
                provider="cos",
            )
        except UnsupportedStorageProviderError as exc:
            stats.failed += 1
            print(f"  FAIL {label}: COS provider is not configured: {exc}")
            continue
        variant = {
            "storage_key": stored.key,
            "url": stored.url,
            "width": None,
            "height": None,
            "content_type": stored.content_type,
            "size_bytes": stored.size_bytes,
        }
        user.avatar_url = stored.url
        user.avatar_storage_provider = stored.provider
        user.avatar_storage_key = stored.key
        user.avatar_variants = {"display": variant, "thumbnail": variant}
        user.avatar_original_filename = source.filename
        user.avatar_processing_status = "ready"
        db.add(user)
        db.commit()
        stats.uploaded += 1
    return stats


def migrate_covers(db, storage: StorageService, settings, args) -> MigrationStats:
    stats = MigrationStats()
    rows = (
        db.query(RouteAsset)
        .filter(RouteAsset.cover_image_url.is_not(None))
        .order_by(RouteAsset.created_at.asc())
        .all()
    )
    print(f"\nLegacy route covers: {len(rows)} rows")
    for route in rows:
        if _already_cos(route.cover_storage_provider) and not args.force:
            stats.skipped += 1
            continue
        stats.planned += 1
        label = f"route_cover:{route.id}"
        try:
            source = _read_source_object(
                route.cover_image_url,
                settings=settings,
                base_url=args.base_url,
                fallback_filename=route.cover_original_filename or f"{route.id}.jpg",
                fallback_content_type=None,
            )
        except Exception as exc:
            stats.failed += 1
            print(f"  FAIL {label}: cannot read source {route.cover_image_url!r}: {exc}")
            continue
        extension = _extension_for(source.filename, source.content_type)
        key = f"users/{route.created_by_user_id}/routes/covers/large-migrated-{route.id}{extension}"
        print(f"  {'UPLOAD' if args.apply else 'PLAN'} {label} -> {key}")
        if not args.apply:
            continue
        try:
            stored = storage.put_bytes(
                key=key,
                content=source.content,
                content_type=source.content_type,
                provider="cos",
            )
        except UnsupportedStorageProviderError as exc:
            stats.failed += 1
            print(f"  FAIL {label}: COS provider is not configured: {exc}")
            continue
        variant = {
            "storage_key": stored.key,
            "url": stored.url,
            "width": None,
            "height": None,
            "content_type": stored.content_type,
            "size_bytes": stored.size_bytes,
        }
        route.cover_image_url = stored.url
        route.cover_storage_provider = stored.provider
        route.cover_storage_key = stored.key
        route.cover_image_variants = {"large": variant, "thumbnail": variant}
        route.cover_original_filename = source.filename
        route.cover_processing_status = "ready"
        db.add(route)
        db.commit()
        stats.uploaded += 1
    return stats


def _read_source_object(
    url_or_path: str | None,
    *,
    settings,
    base_url: str,
    fallback_filename: str,
    fallback_content_type: str | None,
) -> SourceObject:
    if not url_or_path:
        raise FileNotFoundError("empty URL")
    filename = Path(urlparse(url_or_path).path).name or fallback_filename
    content_type = fallback_content_type or _guess_content_type(filename)
    local_path = _local_path_for_static_url(url_or_path, settings)
    if local_path and local_path.exists():
        return SourceObject(local_path.read_bytes(), content_type, filename)
    direct_path = Path(url_or_path)
    if direct_path.exists():
        return SourceObject(direct_path.read_bytes(), content_type, filename)
    download_url = _download_url(url_or_path, base_url)
    if download_url:
        response = httpx.get(download_url, timeout=30)
        response.raise_for_status()
        return SourceObject(
            response.content,
            response.headers.get("content-type", content_type).split(";")[0],
            filename,
        )
    if local_path:
        raise FileNotFoundError(str(local_path))
    raise FileNotFoundError(url_or_path)


def _local_path_for_static_url(url_or_path: str, settings) -> Path | None:
    path = urlparse(url_or_path).path
    mappings = {
        "/static/routes/": Path(settings.route_storage_dir),
        "/static/avatars/": Path(settings.avatar_storage_dir),
        "/static/activity-tracks/": Path(settings.activity_storage_dir),
        "/static/assets/": Path(settings.asset_storage_dir),
    }
    for prefix, root in mappings.items():
        if path.startswith(prefix):
            return root / path.removeprefix(prefix)
    return None


def _download_url(url_or_path: str, base_url: str) -> str | None:
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        return url_or_path
    if url_or_path.startswith("/") and base_url:
        return f"{base_url.rstrip('/')}{url_or_path}"
    return None


def _route_raw_key(row: RouteFile) -> str:
    filename = row.original_filename or Path(urlparse(row.file_url).path).name or row.id
    extension = _extension_for(filename, row.content_type or "")
    return f"users/{row.uploaded_by_user_id}/routes/raw/{row.id}{extension}"


def _extension_for(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix:
        return ".geojson" if suffix == ".json" and content_type == "application/geo+json" else suffix
    guessed = mimetypes.guess_extension(content_type)
    return guessed or ""


def _guess_content_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".gpx":
        return "application/gpx+xml"
    if suffix == ".kml":
        return "application/vnd.google-earth.kml+xml"
    if suffix in {".geojson", ".json"}:
        return "application/geo+json"
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _already_cos(provider: str | None) -> bool:
    return (provider or "").lower() == "cos"


def _safe_database_label(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.scheme:
        return "(configured)"
    host = parsed.hostname or "local"
    database = parsed.path.rsplit("/", 1)[-1] if parsed.path else ""
    return f"{parsed.scheme}://{host}/{database}"


if __name__ == "__main__":
    raise SystemExit(main())
