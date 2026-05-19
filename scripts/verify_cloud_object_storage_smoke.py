from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import paramiko
import requests


DEFAULT_REMOTE_DIR = "/root/smart_outdoor"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify cloud COS read/write browser prerequisites for Smart Outdoor."
    )
    parser.add_argument("--host", default=os.getenv("ECS_HOST"), help="ECS host or IP.")
    parser.add_argument("--user", default=os.getenv("ECS_USER", "root"), help="SSH username.")
    parser.add_argument(
        "--password",
        default=os.getenv("ECS_PASSWORD"),
        help="SSH password. Prefer ECS_PASSWORD env var instead of shell history.",
    )
    parser.add_argument(
        "--key-file",
        default=os.getenv("ECS_KEY_FILE"),
        help="SSH private key file. Overrides password when provided.",
    )
    parser.add_argument(
        "--remote-dir",
        default=os.getenv("SMART_OUTDOOR_REMOTE_DIR", DEFAULT_REMOTE_DIR),
        help="Remote project directory.",
    )
    parser.add_argument(
        "--origin",
        default=os.getenv("SMART_OUTDOOR_PUBLIC_ORIGIN"),
        help="Frontend origin, for example http://112.74.107.171.",
    )
    args = parser.parse_args()

    if not args.host:
        print("Missing ECS host. Set ECS_HOST or pass --host.", file=sys.stderr)
        return 2
    if not args.password and not args.key_file:
        print("Missing SSH credential. Set ECS_PASSWORD or ECS_KEY_FILE.", file=sys.stderr)
        return 2
    origin = (args.origin or f"http://{args.host}").rstrip("/")

    ssh = connect(args)
    try:
        remote_state = remote_probe(ssh, args.remote_dir)
    finally:
        ssh.close()

    token = remote_state["token"]
    route_id = remote_state["route_id"]
    headers = {"Authorization": f"Bearer {token}"}

    print("bucket_acl:", remote_state["acl"].get("CannedACL"))
    print("bucket_referer:", remote_state["referer"])
    print("bucket_cors:", remote_state["cors"])

    credential_response = requests.post(
        f"{origin}/api/storage/upload-credentials",
        headers=headers,
        json={
            "asset_type": "route_track_raw",
            "variant": "raw",
            "content_type": "application/gpx+xml",
            "original_filename": "cors-smoke.gpx",
            "size_bytes": 123,
        },
        timeout=20,
    )
    require(credential_response.status_code == 200, "upload credential should return 200")
    credential = credential_response.json()
    require("q-signature=" in credential["upload_url"], "upload_url should be signed")

    options_response = requests.options(
        credential["upload_url"],
        headers={
            "Origin": origin,
            "Referer": f"{origin}/",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        },
        timeout=20,
    )
    require(options_response.status_code == 200, "COS PUT preflight should return 200")
    require(
        options_response.headers.get("access-control-allow-origin") == origin,
        "COS PUT preflight should echo allowed origin",
    )
    put_response = requests.put(
        credential["upload_url"],
        headers={
            "Origin": origin,
            "Referer": f"{origin}/",
            "Content-Type": "application/gpx+xml",
        },
        data=b"""<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="30.0" lon="120.0"></trkpt><trkpt lat="30.001" lon="120.001"></trkpt></trkseg></trk></gpx>""",
        timeout=20,
    )
    require(put_response.status_code in {200, 204}, "signed COS PUT should upload a probe object")

    avatar_credential_response = requests.post(
        f"{origin}/api/storage/upload-credentials",
        headers=headers,
        json={
            "asset_type": "avatar",
            "variant": "display",
            "content_type": "image/png",
            "original_filename": "avatar-smoke.png",
            "size_bytes": 68,
        },
        timeout=20,
    )
    require(avatar_credential_response.status_code == 200, "avatar credential should return 200")
    avatar_credential = avatar_credential_response.json()
    avatar_put_response = requests.put(
        avatar_credential["upload_url"],
        headers={
            "Origin": origin,
            "Referer": f"{origin}/",
            "Content-Type": "image/png",
        },
        data=(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
            b"\x89\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x01"
            b"\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
        ),
        timeout=20,
    )
    require(
        avatar_put_response.status_code in {200, 204},
        "signed COS PUT should upload an avatar probe object",
    )

    route_response = requests.get(
        f"{origin}/api/routes",
        params={"page_size": 50},
        headers=headers,
        timeout=20,
    )
    require(route_response.status_code == 200, "route list should return 200")
    cover_url = remote_state["cover_url"]
    require(isinstance(cover_url, str) and cover_url, "probe route should have cover URL")
    require("?" not in cover_url, "cover URL should be naked public URL")

    assert_cos_read(cover_url, None, 403, "empty referer")
    assert_cos_read(cover_url, "http://example.com/test.html", 403, "bad referer")
    assert_cos_read(cover_url, f"{origin}/routes", 200, "allowed referer")

    detail_response = requests.get(f"{origin}/api/routes/{route_id}", headers=headers, timeout=20)
    require(detail_response.status_code == 200, "route detail should return 200")
    track_response = requests.get(
        f"{origin}/api/routes/{route_id}/track",
        headers=headers,
        timeout=30,
    )
    require(track_response.status_code == 200, "route track should return 200")
    require(track_response.json().get("point_count", 0) > 0, "route track should have points")

    print("SMOKE_OK")
    return 0


def connect(args) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {"hostname": args.host, "username": args.user, "timeout": 15}
    if args.key_file:
        kwargs["key_filename"] = args.key_file
    else:
        kwargs["password"] = args.password
    ssh.connect(**kwargs)
    return ssh


def remote_probe(ssh: paramiko.SSHClient, remote_dir: str) -> dict:
    cmd = f"cd {quote(remote_dir)} && docker compose exec -T backend python - <<'PY'\n"
    cmd += r"""
import json
from sqlalchemy import select
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.features.routes.model import RouteAsset
from app.features.storage.service import get_storage_service
from app.features.users.model import User

storage = get_storage_service()
client = storage._cos_client()
bucket = storage._cos_bucket()
with SessionLocal() as db:
    user = db.execute(select(User).where(User.status == "active").limit(1)).scalar_one()
    route = db.execute(
        select(RouteAsset)
        .where(RouteAsset.status == "active", RouteAsset.cover_storage_key.is_not(None))
        .order_by(RouteAsset.created_at.desc())
        .limit(1)
    ).scalar_one()
    cover_url = storage.public_url(
        key=route.cover_storage_key,
        provider=route.cover_storage_provider,
    )
    print(json.dumps({
        "token": create_access_token(user.id, user.role),
        "route_id": route.id,
        "cover_url": cover_url,
        "acl": client.get_bucket_acl(Bucket=bucket),
        "referer": client.get_bucket_referer(Bucket=bucket),
        "cors": client.get_bucket_cors(Bucket=bucket),
    }))
"""
    cmd += "\nPY\n"
    _, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    output = stdout.read().decode("utf-8", errors="replace").strip()
    error = stderr.read().decode("utf-8", errors="replace").strip()
    if error:
        print(error, file=sys.stderr)
    if stdout.channel.recv_exit_status() != 0:
        raise SystemExit(1)
    return json.loads(output.splitlines()[-1])


def assert_cos_read(url: str, referer: str | None, expected: int, label: str) -> None:
    headers = {} if referer is None else {"Referer": referer}
    response = requests.get(url, headers=headers, stream=True, timeout=20)
    try:
        require(response.status_code == expected, f"COS read {label} should be {expected}")
    finally:
        response.close()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print("ok:", message)


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
