"""Review 状态管理：标记索引条目的 review 状态，支持纠错和过滤。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .utils import branch_context_path, current_branch


VALID_STATUSES = {"auto", "reviewed", "corrupted"}


def review_mark(root: Path, file_path: str, status: str) -> dict:
    """标记指定文件的 review_status。

    Args:
        root: 项目根目录
        file_path: 文件相对路径
        status: 新状态 (auto/reviewed/corrupted)

    Returns:
        dict 含 path, old_status, new_status
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"无效状态 '{status}'，可选值：{', '.join(sorted(VALID_STATUSES))}")

    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)
    files_path = branch_dir / "index" / "files.jsonl"

    if not files_path.exists():
        raise FileNotFoundError(f"未找到索引文件：{files_path} → 请先运行 scan")

    # 读取所有记录
    lines = files_path.read_text(encoding="utf-8").splitlines()
    records: list[dict] = []
    found = False
    old_status = "auto"
    result: dict = {}

    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("path") == file_path:
            old_status = record.get("review_status", "auto")
            record["review_status"] = status
            found = True
            result = {"path": file_path, "old_status": old_status, "new_status": status}
        records.append(record)

    if not found:
        raise FileNotFoundError(f"未在索引中找到文件：{file_path} → 请检查路径是否正确")

    # 写回
    files_path.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
        encoding="utf-8",
    )

    return result


def review_list(root: Path) -> list[dict]:
    """列出所有文件的 review 状态。

    Returns:
        list[dict] 含 path, review_status, role
    """
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)
    files_path = branch_dir / "index" / "files.jsonl"

    if not files_path.exists():
        raise FileNotFoundError(f"未找到索引文件：{files_path} → 请先运行 scan")

    results: list[dict] = []
    for line in files_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        results.append({
            "path": record.get("path", ""),
            "review_status": record.get("review_status", "auto"),
            "role": record.get("role", ""),
        })

    return results


def get_review_stats(root: Path) -> dict:
    """获取 review 状态分布统计。

    Returns:
        dict 含 total, auto, reviewed, corrupted, distribution
    """
    items = review_list(root)
    total = len(items)
    counts = {"auto": 0, "reviewed": 0, "corrupted": 0}
    for item in items:
        status = item.get("review_status", "auto")
        if status in counts:
            counts[status] += 1
        else:
            counts["auto"] += 1

    return {
        "total": total,
        "auto": counts["auto"],
        "reviewed": counts["reviewed"],
        "corrupted": counts["corrupted"],
        "distribution": {
            k: f"{v} ({v/total:.0%})" if total > 0 else f"{v} (0%)"
            for k, v in counts.items()
        },
    }
