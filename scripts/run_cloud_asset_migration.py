from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_DIR = "/root/smart_outdoor"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the COS asset migration on the cloud deployment through SSH."
    )
    parser.add_argument("--host", default=os.getenv("ECS_HOST"), help="ECS host or IP.")
    parser.add_argument("--user", default=os.getenv("ECS_USER", "root"), help="SSH username.")
    parser.add_argument(
        "--password",
        default=os.getenv("ECS_PASSWORD"),
        help="SSH password. Prefer ECS_PASSWORD env var instead of passing it in shell history.",
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
        "--apply",
        action="store_true",
        help="Apply migration. Without this flag the remote migration runs in dry-run mode.",
    )
    parser.add_argument(
        "--sync-env",
        action="store_true",
        help="Upload local backend/.env to remote backend/.env.production before running.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild backend image before running migration.",
    )
    parser.add_argument(
        "--skip-code-sync",
        action="store_true",
        help="Do not upload Dockerfile and migration script to the remote project before running.",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Public backend base URL used by the remote migration for legacy /static downloads.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to the remote migration script.",
    )
    args = parser.parse_args()

    if not args.host:
        print("Missing ECS host. Set ECS_HOST or pass --host.", file=sys.stderr)
        return 2
    if not args.password and not args.key_file:
        print("Missing SSH credential. Set ECS_PASSWORD or ECS_KEY_FILE.", file=sys.stderr)
        return 2

    ssh = connect(args)
    try:
        if not args.skip_code_sync:
            sync_code(ssh, args.remote_dir)
        if args.sync_env:
            upload_env(ssh, args.remote_dir)
        if args.rebuild or not args.skip_code_sync:
            run_ssh(
                ssh,
                f"cd {quote(args.remote_dir)} && docker compose build backend --progress=plain",
                timeout=900,
                check=True,
            )
        run_ssh(
            ssh,
            f"cd {quote(args.remote_dir)} && docker compose run --rm backend "
            f"python -m app.db.init_db",
            timeout=300,
            check=True,
        )
        migration_args = []
        if args.apply:
            migration_args.append("--apply")
        if args.force:
            migration_args.append("--force")
        if args.base_url:
            migration_args.extend(["--base-url", quote(args.base_url)])
        cmd = (
            f"cd {quote(args.remote_dir)} && docker compose run --rm backend "
            f"python scripts/migrate_assets_to_cos.py {' '.join(migration_args)}"
        )
        return run_ssh(ssh, cmd, timeout=1800, check=False)
    finally:
        ssh.close()


def connect(args) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": args.host,
        "username": args.user,
        "timeout": 15,
    }
    if args.key_file:
        kwargs["key_filename"] = args.key_file
    else:
        kwargs["password"] = args.password
    ssh.connect(**kwargs)
    print(f"Connected to {args.user}@{args.host}")
    return ssh


def upload_env(ssh: paramiko.SSHClient, remote_dir: str) -> None:
    local_env = PROJECT_ROOT / "backend" / ".env"
    if not local_env.exists():
        raise FileNotFoundError(local_env)
    remote_path = f"{remote_dir}/backend/.env.production"
    sftp = ssh.open_sftp()
    try:
        sftp.put(str(local_env), remote_path)
    finally:
        sftp.close()
    print(f"Uploaded backend/.env to {remote_path}")


def sync_code(ssh: paramiko.SSHClient, remote_dir: str) -> None:
    files = [
        (PROJECT_ROOT / "backend" / "Dockerfile", f"{remote_dir}/backend/Dockerfile"),
        (PROJECT_ROOT / "backend" / "pyproject.toml", f"{remote_dir}/backend/pyproject.toml"),
        (
            PROJECT_ROOT / "backend" / "scripts" / "migrate_assets_to_cos.py",
            f"{remote_dir}/backend/scripts/migrate_assets_to_cos.py",
        ),
    ]
    run_ssh(ssh, f"mkdir -p {quote(remote_dir + '/backend/scripts')}", timeout=60, check=True)
    sftp = ssh.open_sftp()
    try:
        for local_path, remote_path in files:
            sftp.put(str(local_path), remote_path)
            print(f"Uploaded {local_path.relative_to(PROJECT_ROOT)} to {remote_path}")
        upload_tree(
            sftp,
            PROJECT_ROOT / "backend" / "app",
            f"{remote_dir}/backend/app",
        )
    finally:
        sftp.close()


def upload_tree(sftp: paramiko.SFTPClient, local_root: Path, remote_root: str) -> None:
    ensure_remote_dir(sftp, remote_root)
    for local_path in local_root.rglob("*"):
        relative = local_path.relative_to(local_root)
        remote_path = f"{remote_root}/{relative.as_posix()}"
        if local_path.is_dir():
            ensure_remote_dir(sftp, remote_path)
            continue
        if should_skip_upload(local_path):
            continue
        ensure_remote_dir(sftp, str(Path(remote_path).parent).replace("\\", "/"))
        sftp.put(str(local_path), remote_path)
    print(f"Uploaded {local_root.relative_to(PROJECT_ROOT)} to {remote_root}")


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = [part for part in remote_dir.replace("\\", "/").split("/") if part]
    path = ""
    for part in parts:
        path += f"/{part}"
        try:
            sftp.stat(path)
        except FileNotFoundError:
            sftp.mkdir(path)


def should_skip_upload(path: Path) -> bool:
    return path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}


def run_ssh(
    ssh: paramiko.SSHClient,
    cmd: str,
    *,
    timeout: int,
    check: bool,
) -> int:
    print(f"\n$ {redact(cmd)}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            sys.stdout.write(stdout.channel.recv(4096).decode("utf-8", errors="replace"))
            sys.stdout.flush()
        if stderr.channel.recv_stderr_ready():
            sys.stderr.write(stderr.channel.recv_stderr(4096).decode("utf-8", errors="replace"))
            sys.stderr.flush()
    remaining_out = stdout.read().decode("utf-8", errors="replace")
    remaining_err = stderr.read().decode("utf-8", errors="replace")
    if remaining_out:
        sys.stdout.write(remaining_out)
    if remaining_err:
        sys.stderr.write(remaining_err)
    code = stdout.channel.recv_exit_status()
    if check and code != 0:
        raise SystemExit(code)
    return code


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def redact(value: str) -> str:
    for name in ("COS_SECRET_KEY", "COS_SECRET_ID", "ECS_PASSWORD"):
        secret = os.getenv(name)
        if secret:
            value = value.replace(secret, "***")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
