"""扫描状态查询。"""

from __future__ import annotations

import json
from pathlib import Path


def get_status(root: Path) -> dict:
    """返回项目扫描状态。"""
    latest_path = root / ".project-context" / "scans" / "latest.json"
    if not latest_path.exists():
        return {
            "project_name": root.name,
            "status": "未扫描",
            "message": "尚未运行 scan 命令。请先运行 forge-memory scan。",
        }
    data = json.loads(latest_path.read_text(encoding="utf-8"))
    return {
        "project_name": root.name,
        "status": data.get("status", "unknown"),
        "last_scan": data.get("finished_at", ""),
        "scan_id": data.get("scan_id", ""),
        "file_count": data.get("file_count", 0),
        "module_count": data.get("module_count", 0),
        "changed_files": data.get("changed_files", 0),
        "unchanged_files": data.get("unchanged_files", 0),
        "new_files": data.get("new_files", 0),
        "deleted_files": data.get("deleted_files", 0),
    }
