from __future__ import annotations

from fastapi.testclient import TestClient


def upload_object(
    client: TestClient,
    headers: dict[str, str],
    *,
    asset_type: str,
    filename: str,
    content: bytes,
    content_type: str,
    variant: str | None = None,
) -> dict:
    credential_response = client.post(
        "/api/storage/upload-credentials",
        headers=headers,
        json={
            "asset_type": asset_type,
            "variant": variant,
            "content_type": content_type,
            "original_filename": filename,
            "size_bytes": len(content),
        },
    )
    assert credential_response.status_code == 200, credential_response.text
    credential = credential_response.json()
    upload_response = client.put(
        credential["upload_url"],
        headers={**headers, "Content-Type": content_type},
        content=content,
    )
    assert upload_response.status_code == 200, upload_response.text
    return credential


def image_asset(
    client: TestClient,
    headers: dict[str, str],
    *,
    asset_type: str,
    original_filename: str,
    variants: dict[str, tuple[bytes, int, int]],
) -> dict:
    variant_metadata: dict[str, dict] = {}
    first_key: str | None = None
    first_url: str | None = None
    for variant, (content, width, height) in variants.items():
        credential = upload_object(
            client,
            headers,
            asset_type=asset_type,
            variant=variant,
            filename=f"{variant}.webp",
            content=content,
            content_type="image/webp",
        )
        if first_key is None:
            first_key = credential["storage_key"]
            first_url = credential["public_url"]
        variant_metadata[variant] = {
            "storage_key": credential["storage_key"],
            "url": credential["public_url"],
            "width": width,
            "height": height,
            "content_type": "image/webp",
            "size_bytes": len(content),
        }
    return {
        "storage_provider": "local",
        "storage_key": first_key,
        "url": first_url,
        "original_filename": original_filename,
        "processing_status": "ready",
        "variants": variant_metadata,
    }


def upload_route_complete(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    content: bytes,
    filename: str = "demo.gpx",
    content_type: str = "application/gpx+xml",
    visibility: str = "private",
    description: str | None = None,
    manual_tags: dict | None = None,
    cover_image: dict | None = None,
) -> dict:
    response = post_route_complete(
        client,
        headers,
        name=name,
        content=content,
        filename=filename,
        content_type=content_type,
        visibility=visibility,
        description=description,
        manual_tags=manual_tags,
        cover_image=cover_image,
    )
    assert response.status_code == 200, response.text
    return response.json()


def post_route_complete(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    content: bytes,
    filename: str = "demo.gpx",
    content_type: str = "application/gpx+xml",
    visibility: str = "private",
    description: str | None = None,
    manual_tags: dict | None = None,
    cover_image: dict | None = None,
):
    """Upload raw content through storage, then POST the route complete payload."""
    track = upload_object(
        client,
        headers,
        asset_type="route_track_raw",
        filename=filename,
        content=content,
        content_type=content_type,
    )
    file_type = filename.rsplit(".", 1)[-1].lower()
    if file_type == "json":
        file_type = "geojson"
    return client.post(
        "/api/routes/upload",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "visibility": visibility,
            "manual_tags": manual_tags or {},
            "track_file": {
                "storage_provider": track["storage_provider"],
                "storage_key": track["storage_key"],
                "file_url": track["public_url"],
                "file_type": file_type,
                "content_type": content_type,
                "size_bytes": len(content),
                "original_filename": filename,
            },
            "cover_image": cover_image,
        },
    )
