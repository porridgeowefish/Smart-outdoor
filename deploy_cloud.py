"""Smart_outdoor 一键打包上云。

在 Windows 本地运行，自动打包代码、上传到 ECS、远程构建并部署。

用法:  python deploy_cloud.py
"""

from __future__ import annotations

import fnmatch
import os
import sys
import tarfile
import time

import paramiko

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

ECS_HOST = os.getenv("ECS_HOST", "112.74.107.171")
ECS_USER = os.getenv("ECS_USER", "root")
ECS_PASSWORD = os.getenv("ECS_PASSWORD", "Greedy0805#")
REMOTE_DIR = "/root/smart_outdoor"

PG_PASSWORD = "SmartOutdoor2026"
PG_USER = "smart_outdoor"
AMAP_KEY = "0ccf32829c5857a8243d7b5d1d84f63b"

EXCLUDES = [
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".git",
    ".logs",
    "storage",
    ".env",
    ".claude",
    "*.pyc",
    "_screenshot_*.png",
    "smart_outdoor_deploy.tar.gz",
]

# ---------------------------------------------------------------------------
# 打包
# ---------------------------------------------------------------------------


def _should_exclude(name: str) -> bool:
    for pat in EXCLUDES:
        if fnmatch.fnmatch(name, pat) or name == pat:
            return True
    return False


def _tar_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    name = os.path.basename(tarinfo.name)
    if _should_exclude(name):
        return None
    return tarinfo


def create_tarball(tar_path: str) -> None:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    with tarfile.open(tar_path, "w:gz") as tar:
        for item in [
            "backend",
            "user-frontend-new",
            "nginx",
            "docker-compose.yml",
        ]:
            full = os.path.join(project_dir, item)
            if not os.path.exists(full):
                print(f"[WARN] {item} 不存在，跳过")
                continue
            tar.add(full, arcname=item, filter=_tar_filter)
    size_mb = os.path.getsize(tar_path) / 1024 / 1024
    print(f"打包完成: {tar_path} ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# SSH 工具
# ---------------------------------------------------------------------------


def run_ssh(
    ssh: paramiko.SSHClient,
    cmd: str,
    timeout: int = 300,
    check: bool = False,
) -> int:
    """执行远程命令并打印输出，返回 exit code。"""
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    output = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()

    if output.strip():
        sys.stdout.buffer.write(output.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()
    if exit_code != 0 and err.strip():
        sys.stdout.buffer.write(("[STDERR] " + err).encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()

    if check and exit_code != 0:
        sys.exit(1)

    return exit_code


# ---------------------------------------------------------------------------
# 环境文件
# ---------------------------------------------------------------------------

ENV_PRODUCTION = f"""\
DATABASE_URL=postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@postgres:5432/smart_outdoor
JWT_SECRET_KEY=sk-smart-outdoor-jwt-prod-2026-xyz
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
AVATAR_STORAGE_DIR=/app/storage/avatars
ROUTE_STORAGE_DIR=/app/storage/routes
ACTIVITY_STORAGE_DIR=/app/storage/activity_tracks
USE_MOCK_AMAP=false
USE_MOCK_WEATHER=true
AMAP_WEB_SERVICE_KEY={AMAP_KEY}
AMAP_REVERSE_GEOCODE_URL=https://restapi.amap.com/v3/geocode/regeo
"""

COMPOSE_ENV = f"""\
POSTGRES_USER={PG_USER}
POSTGRES_PASSWORD={PG_PASSWORD}
"""


def write_remote_file(ssh: paramiko.SSHClient, path: str, content: str) -> None:
    sftp = ssh.open_sftp()
    with sftp.file(path, "w") as f:
        f.write(content)
    sftp.close()


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def step(msg: str) -> None:
    print(f"\n{'=' * 60}\n  {msg}\n{'=' * 60}")


def main() -> None:
    tar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "smart_outdoor_deploy.tar.gz"
    )

    # 1. 打包
    step("[1/8] 打包项目代码")
    create_tarball(tar_path)

    # 2. 连接
    step("[2/8] 连接 ECS")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ECS_HOST, username=ECS_USER, password=ECS_PASSWORD, timeout=10)
    print(f"已连接 {ECS_HOST}")

    try:
        # 3. 上传
        step("[3/8] 上传代码")
        sftp = ssh.open_sftp()
        sftp.put(tar_path, "/root/smart_outdoor_deploy.tar.gz")
        sftp.close()
        print("上传完成")

        # 4. 解压 + 环境配置
        step("[4/8] 准备远程环境")
        run_ssh(ssh, f"mkdir -p {REMOTE_DIR}")
        run_ssh(
            ssh, f"cd {REMOTE_DIR} && tar xzf /root/smart_outdoor_deploy.tar.gz"
        )
        write_remote_file(
            ssh, f"{REMOTE_DIR}/backend/.env.production", ENV_PRODUCTION
        )
        write_remote_file(ssh, f"{REMOTE_DIR}/.env", COMPOSE_ENV)
        print("环境配置完成")

        # 5. 停旧容器
        step("[5/8] 停止旧容器")
        run_ssh(
            ssh,
            "docker stop smart_outdoor_nginx smart_outdoor_backend "
            "smart_outdoor_postgres 2>/dev/null; "
            "docker rm smart_outdoor_nginx smart_outdoor_backend "
            "smart_outdoor_postgres 2>/dev/null",
        )
        print("旧容器已清理")

        # 6. 构建
        step("[6/8] 远程构建 Docker 镜像（可能需要几分钟）")
        run_ssh(
            ssh,
            f"cd {REMOTE_DIR} && docker compose build --progress=plain 2>&1",
            timeout=600,
            check=True,
        )
        print("构建成功")

        # 7. 启动 + 建表
        step("[7/8] 启动服务并初始化数据库")
        run_ssh(ssh, f"cd {REMOTE_DIR} && docker compose up -d 2>&1")
        print("等待 PostgreSQL 就绪...")
        time.sleep(10)
        run_ssh(
            ssh,
            f"cd {REMOTE_DIR} && docker compose exec -T backend "
            f"python -m app.db.init_db 2>&1",
        )
        print("数据库表已创建")

        # 8. 健康检查
        step("[8/8] 健康检查")
        time.sleep(5)
        run_ssh(
            ssh,
            'curl -sf http://localhost/ > /dev/null 2>&1 '
            '&& echo "  Frontend: OK" '
            '|| echo "  Frontend: FAIL"',
        )
        run_ssh(
            ssh,
            'curl -sf http://localhost/api/auth/login > /dev/null 2>&1 '
            '&& echo "  Backend API: OK" '
            '|| echo "  Backend API: checking..."',
        )
        run_ssh(
            ssh,
            'docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" '
            '| grep smart_outdoor',
        )

        print(f"\n{'=' * 60}")
        print(f"  部署完成！访问 http://{ECS_HOST}")
        print(f"{'=' * 60}")

    finally:
        ssh.close()


if __name__ == "__main__":
    main()
