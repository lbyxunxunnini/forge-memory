"""状态检查：检查环境依赖和索引健康状态。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .status import get_status
from .utils import branch_context_path, current_branch


def check_environment() -> list[dict]:
    """检查环境依赖。"""
    checks = []

    # Python 版本
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append({
        "name": "Python 版本",
        "status": "ok" if sys.version_info >= (3, 10) else "error",
        "value": py_version,
        "message": "" if sys.version_info >= (3, 10) else "需要 Python 3.10+",
    })

    # Git
    git_path = shutil.which("git")
    if git_path:
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            git_version = result.stdout.strip()
            checks.append({
                "name": "Git",
                "status": "ok",
                "value": git_version,
                "message": "",
            })
        except Exception:
            checks.append({
                "name": "Git",
                "status": "warning",
                "value": "已安装",
                "message": "无法获取版本信息",
            })
    else:
        checks.append({
            "name": "Git",
            "status": "error",
            "value": "未安装",
            "message": "commit 历史功能需要 git",
        })

    return checks


def check_index(root: Path) -> list[dict]:
    """检查索引健康状态。"""
    checks = []
    context = root / ".project-context"

    # context.json
    ctx_path = context / "context.json"
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
            checks.append({
                "name": "context.json",
                "status": "ok",
                "value": f"分支: {ctx.get('active_branch', 'unknown')}",
                "message": "",
            })
        except json.JSONDecodeError:
            checks.append({
                "name": "context.json",
                "status": "error",
                "value": "JSON 解析失败",
                "message": "文件可能损坏",
            })
    else:
        checks.append({
            "name": "context.json",
            "status": "error",
            "value": "不存在",
            "message": "请运行 init 命令",
        })

    # project-summary.md
    summary_path = context / "project-summary.md"
    if summary_path.exists():
        size = summary_path.stat().st_size
        checks.append({
            "name": "project-summary.md",
            "status": "ok" if size > 100 else "warning",
            "value": f"{size} bytes",
            "message": "" if size > 100 else "内容可能不完整",
        })
    else:
        checks.append({
            "name": "project-summary.md",
            "status": "error",
            "value": "不存在",
            "message": "请运行 scan 命令",
        })

    # 索引文件
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)
    files_path = branch_dir / "index" / "files.jsonl"
    if files_path.exists():
        line_count = sum(1 for line in files_path.read_text(encoding="utf-8").splitlines() if line.strip())
        checks.append({
            "name": "files.jsonl",
            "status": "ok" if line_count > 0 else "warning",
            "value": f"{line_count} 个文件",
            "message": "",
        })
    else:
        checks.append({
            "name": "files.jsonl",
            "status": "error",
            "value": "不存在",
            "message": "请运行 scan 命令",
        })

    # SQLite 数据库
    db_path = branch_dir / "forge-memory.db"
    if db_path.exists():
        size = db_path.stat().st_size
        checks.append({
            "name": "forge-memory.db",
            "status": "ok",
            "value": f"{size} bytes",
            "message": "",
        })
    else:
        checks.append({
            "name": "forge-memory.db",
            "status": "info",
            "value": "不存在",
            "message": "可选：运行 import-db 创建",
        })

    return checks


def doctor(root: Path) -> int:
    """运行状态检查。"""
    print(f"项目：{root.name}")
    print(f"路径：{root}")
    print()

    # 环境检查
    print("环境检查：")
    env_checks = check_environment()
    for check in env_checks:
        status_icon = "✓" if check["status"] == "ok" else "✗" if check["status"] == "error" else "⚠"
        print(f"  {status_icon} {check['name']}: {check['value']}")
        if check["message"]:
            print(f"    {check['message']}")
    print()

    # 索引检查
    print("索引检查：")
    index_checks = check_index(root)
    for check in index_checks:
        status_icon = "✓" if check["status"] == "ok" else "✗" if check["status"] == "error" else "ℹ" if check["status"] == "info" else "⚠"
        print(f"  {status_icon} {check['name']}: {check['value']}")
        if check["message"]:
            print(f"    {check['message']}")

    # 总结
    print()
    errors = sum(1 for c in env_checks + index_checks if c["status"] == "error")
    warnings = sum(1 for c in env_checks + index_checks if c["status"] == "warning")

    if errors > 0:
        print(f"发现 {errors} 个错误，{warnings} 个警告。请修复后重试。")
        return 1
    elif warnings > 0:
        print(f"发现 {warnings} 个警告。建议处理以获得最佳体验。")
        return 0
    else:
        print("所有检查通过！")
        return 0
