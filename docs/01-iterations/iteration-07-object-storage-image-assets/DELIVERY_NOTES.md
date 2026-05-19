# Delivery Notes

Status: implemented
Owner: project maintainer
Last reviewed: 2026-05-18
Source of truth: implementation, generated OpenAPI, and this iteration document set.

## Delivered

```text
Documented the confirmed Iteration 07 architecture:
- Frontend direct upload through temporary credentials.
- Images are compressed on the frontend; original images are not retained.
- Route raw tracks are directly uploaded and then parsed by backend from storage_key.
- Full derived track_geojson is stored in object storage.
- High-fidelity track_preview_geojson is stored in database.
- Preview uses Douglas-Peucker with tolerance_m=10 and max_segment_length_m=150.
- Tencent COS provider is supported through `qcloud-cos-python-sdk-v5`; local provider remains the default for tests and development.
- `/api/routes/upload` now receives JSON metadata complete instead of multipart form-data.
- Profile avatar upload now uses display / thumbnail variants and `PATCH /api/me`.
- Route detail renders preview first and then loads the full derived track through `GET /api/routes/{route_id}/track`.
```

## Tests Run

```text
backend: python -m pytest
result: 104 passed

frontend: npm run lint
result: tsc --noEmit passed
```

## Legacy Data Migration

```text
Migration script:
backend/scripts/migrate_assets_to_cos.py

Cloud automation wrapper:
scripts/run_cloud_asset_migration.py

Dry run:
cd backend
python scripts/migrate_assets_to_cos.py

Apply:
cd backend
python scripts/migrate_assets_to_cos.py --apply
```

The script uses `backend/.env` by default. Before applying, set:

```text
STORAGE_PROVIDER=cos
COS_SECRET_ID=...
COS_SECRET_KEY=...
COS_BUCKET=...
COS_REGION=...
```

If the script runs outside the cloud server and legacy `/static/...` files are only reachable through the deployed backend, pass:

```text
python scripts/migrate_assets_to_cos.py --base-url https://your-api-domain --apply
```

To run the same migration through SSH against the deployed Docker Compose stack:

```text
python scripts/run_cloud_asset_migration.py --rebuild
python scripts/run_cloud_asset_migration.py --rebuild --apply
```

The wrapper reads `ECS_HOST`, `ECS_USER`, `ECS_PASSWORD` or `ECS_KEY_FILE`, and `SMART_OUTDOOR_REMOTE_DIR` from environment variables. Runtime configuration is owned by `backend/.env`; do not recreate a separate `backend/.env.production` for migration or deploy.

Migration scope:

```text
route_files: uploads legacy raw GPX/KML/GeoJSON files to COS and updates storage metadata.
route_analysis_snapshots: uploads legacy track_geojson as full derived GeoJSON to COS and backfills preview metadata.
users: uploads legacy avatar_url images to COS and backfills avatar variants metadata.
route_assets: uploads legacy cover_image_url images to COS and backfills cover variants metadata.
```

Cloud migration verification on 2026-05-18:

```text
route_files migrated to COS: 10 / 10
derived track_geojson files migrated to COS: 10 / 10
route cover images migrated to COS: 9 / 9
user avatars migrated to COS: 1 / 1
```

Cloud runtime verification on 2026-05-18:

```text
frontend public entry: 200
GET /api/routes: 200
GET /api/routes/{route_id}: 200
GET /api/routes/{route_id}/track: 200
COS cover image fetch through returned naked URL with allowed Referer: 200 image/jpeg
COS cover image fetch with empty Referer: 403
COS cover image fetch with untrusted Referer: 403
sample full track point_count: 20647
```

## Cloud Hotfix Notes

```text
The runtime access model is public-read COS bucket plus Referer anti-hotlink protection.
The backend returns naked COS public URLs for route covers, route files, and user avatars,
so COS Referer rules can block empty or untrusted browser requests.

Upload URLs remain signed PUT URLs because frontend direct upload still needs temporary
write permission.

Cloud COS settings verified on 2026-05-18:
- bucket ACL: public-read
- Referer type: White-List
- allowed Referers: deployed server IP and port 80 variant
- empty Referer: Deny
```

## Upload CORS Incident Follow-Up

```text
Incident report:
docs/01-iterations/iteration-07-object-storage-image-assets/INCIDENT_REPORT_2026-05-19_UPLOAD_CORS.md

Root cause:
Frontend direct upload used signed COS PUT URLs, but the bucket had no CORS rule.
Browser OPTIONS preflight failed with 403, while backend/local-provider tests still passed.

Cloud fix verified on 2026-05-19:
- COS CORS AllowedOrigin: deployed frontend origin and :80 variant
- COS CORS AllowedMethod: PUT, GET, HEAD
- COS CORS AllowedHeader: *
- COS CORS ExposeHeader: ETag, x-cos-request-id, x-cos-trace-id
- COS CORS MaxAgeSeconds: 600
- POST /api/storage/upload-credentials: 200
- OPTIONS signed PUT upload_url: 200
- signed PUT route track probe object: 200
- signed PUT avatar probe object: 200
- empty Referer read: 403
- untrusted Referer read: 403
- allowed Referer read: 200

Reusable smoke script:
python scripts/verify_cloud_object_storage_smoke.py
```

## Risks

```text
COS requires runtime configuration:
STORAGE_PROVIDER=cos
COS_SECRET_ID
COS_SECRET_KEY
COS_BUCKET
COS_REGION
optional COS_TOKEN
optional COS_CDN_BASE_URL

The backend loads configuration from `backend/.env` by default. This is the single runtime source of truth for local development and cloud deployment.
`backend/config/app.local.env` remains an optional fallback for experiments, not a second maintained runtime config.
`SMART_OUTDOOR_ENV_FILE` can point to another config file only for temporary diagnostics.
Real config files and `deploy_cloud.py` are ignored by git.

Existing route_analysis_snapshots.track_geojson remains a legacy compatibility field.
New uploads store the high-fidelity preview in the database and the full derived track in object storage.
```
