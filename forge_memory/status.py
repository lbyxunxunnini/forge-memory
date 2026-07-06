"""扫描状态查询。"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import branch_context_path, current_branch


def get_status(root: Path) -> dict:
    """返回项目扫描状态。"""
    context = root / ".project-context"
    ctx_path = context / "context.json"

    # 读取分支信息
    branch = "unknown"
    if ctx_path.exists():
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        branch = ctx.get("active_branch", current_branch(root))
    else:
        branch = current_branch(root)

    branch_dir = branch_context_path(root, branch)
    latest_path = branch_dir / "scans" / "latest.json"

    if not latest_path.exists():
        return {
            "project_name": root.name,
            "branch": branch,
            "status": "未扫描",
            "message": "尚未运行 scan 命令。请先运行 forge-memory scan。",
        }

    data = json.loads(latest_path.read_text(encoding="utf-8"))

    # 统计 commit 数量
    commits_path = branch_dir / "index" / "commits.jsonl"
    commit_count = 0
    if commits_path.exists():
        commit_count = sum(1 for line in commits_path.read_text(encoding="utf-8").splitlines() if line.strip())

    return {
        "project_name": root.name,
        "branch": branch,
        "status": data.get("status", "unknown"),
        "last_scan": data.get("finished_at", ""),
        "scan_id": data.get("scan_id", ""),
        "file_count": data.get("file_count", 0),
        "module_count": data.get("module_count", 0),
        "changed_files": data.get("changed_files", 0),
        "unchanged_files": data.get("unchanged_files", 0),
        "new_files": data.get("new_files", 0),
        "deleted_files": data.get("deleted_files", 0),
        "commit_count": commit_count,
    }
