"""扫描状态查询。"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .utils import branch_context_path, current_branch


def _count_project_files(root: Path) -> int:
    """统计项目实际文件数（排除排除目录）。"""
    from .utils import EXCLUDE_DIRS, EXCLUDE_SUFFIXES

    count = 0
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for filename in filenames:
            path = current_path / filename
            if path.suffix.lower() not in EXCLUDE_SUFFIXES:
                count += 1
    return count


def _calculate_health(data: dict, branch_dir: Path, root: Path) -> dict:
    """计算索引健康度指标。"""
    health = {}

    # 1. 文件覆盖率
    indexed_files = data.get("file_count", 0)
    actual_files = _count_project_files(root)
    if actual_files > 0:
        coverage = indexed_files / actual_files
        health["file_coverage"] = f"{coverage:.1%}"
        health["file_coverage_status"] = "good" if coverage > 0.8 else "warning" if coverage > 0.5 else "low"
    else:
        health["file_coverage"] = "N/A"
        health["file_coverage_status"] = "unknown"

    # 2. 索引新鲜度
    last_scan = data.get("finished_at", "")
    if last_scan:
        try:
            scan_time = datetime.fromisoformat(last_scan.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - scan_time).total_seconds() / 3600
            health["index_age_hours"] = round(age_hours, 1)
            health["index_freshness"] = "fresh" if age_hours < 24 else "stale" if age_hours < 168 else "very_stale"
        except (ValueError, TypeError):
            health["index_age_hours"] = "N/A"
            health["index_freshness"] = "unknown"

    # 3. content_hash 过期比例
    files_path = branch_dir / "index" / "files.jsonl"
    if files_path.exists():
        total = 0
        with_hash = 0
        for line in files_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    f = json.loads(line)
                    total += 1
                    if f.get("content_hash"):
                        with_hash += 1
                except json.JSONDecodeError:
                    continue
        if total > 0:
            health["hash_coverage"] = f"{with_hash / total:.1%}"
        else:
            health["hash_coverage"] = "N/A"

    return health


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

    # 计算健康度
    health = _calculate_health(data, branch_dir, root)

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
        "health": health,
    }
