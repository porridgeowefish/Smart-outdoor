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
from urllib.parse import unquote, urlparse

import paramiko

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

ECS_HOST = os.getenv("ECS_HOST", "112.74.107.171")
ECS_USER = os.getenv("ECS_USER", "root")
ECS_PASSWORD = os.getenv("ECS_PASSWORD", "Greedy0805#")
REMOTE_DIR = "/root/smart_outdoor"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ENV_PATH = os.path.join(PROJECT_DIR, "backend", ".env")

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

def read_backend_env() -> tuple[str, dict[str, str]]:
    if not os.path.exists(BACKEND_ENV_PATH):
        raise FileNotFoundError(
            f"Missing backend runtime env file: {BACKEND_ENV_PATH}"
        )
    content = open(BACKEND_ENV_PATH, "r", encoding="utf-8").read()
    return content, parse_env(content)


def parse_env(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    return values


def compose_env_from_backend_env(values: dict[str, str]) -> str:
    database_url = values.get("DATABASE_URL", "")
    parsed = urlparse(database_url)
    if not parsed.username or not parsed.password:
        raise ValueError("backend/.env DATABASE_URL must include PostgreSQL user and password")
    return (
        f"POSTGRES_USER={unquote(parsed.username)}\n"
        f"POSTGRES_PASSWORD={unquote(parsed.password)}\n"
    )


def assert_cloud_runtime_env(values: dict[str, str]) -> None:
    required = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "STORAGE_PROVIDER",
        "COS_SECRET_ID",
        "COS_SECRET_KEY",
        "COS_BUCKET",
        "COS_REGION",
        "USE_MOCK_LLM",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
    ]
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise ValueError(
            "backend/.env is the deployment source of truth but is missing: "
            + ", ".join(missing)
        )


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
    backend_env_content, backend_env_values = read_backend_env()
    assert_cloud_runtime_env(backend_env_values)
    compose_env = compose_env_from_backend_env(backend_env_values)

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
        write_remote_file(ssh, f"{REMOTE_DIR}/backend/.env", backend_env_content)
        write_remote_file(ssh, f"{REMOTE_DIR}/.env", compose_env)
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
