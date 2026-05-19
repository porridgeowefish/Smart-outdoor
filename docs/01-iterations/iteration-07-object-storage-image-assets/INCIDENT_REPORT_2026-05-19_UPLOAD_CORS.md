# Incident Report: Upload CORS Failure

Date: 2026-05-19
Status: resolved
Iteration: 07 Object Storage + Image Assets

## Summary

Avatar upload and route upload both failed in the deployed frontend with `fail to fetch`.

The direct cause was missing Tencent COS CORS configuration. The frontend uploads files
directly to a signed COS `PUT` URL, so the browser sends an `OPTIONS` preflight before
the upload. The bucket had no CORS rules, and COS returned:

```text
403 CORSResponse: This CORS request is not allowed
```

## Root Cause

The object storage work verified the read path but not the browser write path.

Verified before the incident:

```text
Public naked COS URL with allowed Referer: 200
Public naked COS URL with empty Referer: 403
Public naked COS URL with untrusted Referer: 403
GET /api/routes: 200
GET /api/routes/{route_id}: 200
GET /api/routes/{route_id}/track: 200
```

Missing verification:

```text
Browser-equivalent OPTIONS preflight to signed PUT upload_url
Actual frontend direct upload for avatar
Actual frontend direct upload for route raw track and cover image
```

## Trigger

The read model was changed to:

```text
public-read bucket + Referer anti-hotlink + naked COS URLs
```

That fixed browser rendering, but it did not prove direct upload was usable. Direct upload
is governed by CORS, not by the same Referer read checks.

## Why Tests Missed It

The automated tests used the local storage provider and FastAPI TestClient. Those tests
verified API contracts and local upload behavior, but they could not exercise browser CORS
or Tencent COS bucket configuration.

The test suite also lacked a cloud smoke test for:

```text
POST /api/storage/upload-credentials
OPTIONS signed PUT URL with Origin and Access-Control-Request-* headers
COS CORS rule presence
actual browser upload path
```

## Corrective Actions

Applied cloud configuration:

```text
bucket ACL: public-read
Referer type: White-List
Empty Referer: Deny
Allowed Referers: deployed server IP and :80 variant
CORS AllowedOrigin: deployed frontend origin and :80 variant
CORS AllowedMethod: PUT, GET, HEAD
CORS AllowedHeader: *
CORS ExposeHeader: ETag, x-cos-request-id, x-cos-trace-id
CORS MaxAgeSeconds: 600
```

Added project checks:

```text
backend storage unit test: COS public_url remains unsigned
backend storage unit test: COS upload_url remains signed PUT
cloud smoke script: scripts/verify_cloud_object_storage_smoke.py
```

Cloud verification after fix:

```text
POST /api/storage/upload-credentials: 200
OPTIONS signed PUT upload_url: 200
access-control-allow-origin: deployed frontend origin
signed PUT route track probe object: 200
signed PUT avatar probe object: 200
empty Referer read: 403
untrusted Referer read: 403
allowed Referer read: 200
GET /api/routes/{route_id}/track: 200
```

## Long-Term Rule

Any future frontend direct-upload work to COS, S3, OSS, or similar object storage is not
complete until all four storage controls are verified together:

```text
ACL or bucket policy
CORS for browser write path
Referer / anti-hotlink policy for naked public read path
signed URL behavior for temporary write or private read paths
```

Backend tests are necessary but not sufficient. A cloud/browser-equivalent smoke test is
required before calling the slice complete.

## Follow-up: Avatar Update Persisted Failure

After the CORS fix, avatar image bytes could be uploaded but refreshing the profile still
showed the old avatar. Cloud logs showed:

```text
POST /api/storage/upload-credentials: 200
POST /api/storage/upload-credentials: 200
PATCH /api/me: 422 Unprocessable Entity
```

Root cause:

```text
The frontend reused UploadedObject directly inside avatar.variants.
UploadedObject includes storage_provider, but StorageObjectMetadata forbids extra fields.
Pydantic rejected the business-complete PATCH, so the database never changed.
```

Correction:

```text
Strip upload-only fields before sending ImageAssetMetadata variants.
Show avatar upload errors in the profile page instead of logging only to console.
Verify existing-avatar replacement, not only first-time avatar setup.
```

Additional deployment issue found during verification:

```text
The deployment path had two runtime env sources: backend/.env and backend/.env.production.
backend/.env.production missed COS and LLM settings, so a direct Docker Compose run could
fall back to local provider and mock services.
```

New permanent rule:

```text
Object-storage closure must verify the exact frontend payload shape, the business
complete API write, the refresh/read API result, and deployment-time provider config.
backend/.env is the single runtime source of truth for local development and cloud deploy.
Do not restore backend/.env.production or duplicate runtime config inside deploy scripts.
```
