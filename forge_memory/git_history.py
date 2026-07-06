"""Git 历史扫描：commits.jsonl、commit_files.jsonl。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _git(root: Path, args: list[str], timeout: int = 30) -> str:
    """运行 git 命令，返回 stdout。"""
    result = subprocess.run(
        ["git"] + args,
        cwd=root, capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout


def scan_git_history(root: Path, max_commits: int = 50) -> dict:
    """解析 git log，返回 {commits: [...], commit_files: [...]}。"""
    # 使用 --format + --numstat 一次性获取 commit 信息和文件变更
    raw = _git(root, [
        "log", f"-{max_commits}",
        "--format=COMMIT_START%n%H%n%h%n%an%n%ai%n%s",
        "--numstat",
    ])

    commits = []
    commit_files = []
    current_commit = None

    for line in raw.splitlines():
        if line == "COMMIT_START":
            if current_commit:
                commits.append(current_commit)
            current_commit = {
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
            }
            continue

        if current_commit is None:
            continue

        # 解析 commit 头部字段
        if "hash" not in current_commit:
            current_commit["hash"] = line
            continue
        if "short_hash" not in current_commit:
            current_commit["short_hash"] = line
            continue
        if "author" not in current_commit:
            current_commit["author"] = line
            continue
        if "date" not in current_commit:
            current_commit["date"] = line
            continue
        if "message" not in current_commit:
            current_commit["message"] = line
            continue

        # 解析 numstat 行：insertions\tdeletions\tfilepath
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            ins, dels, filepath = parts
            ins_val = int(ins) if ins != "-" else 0
            dels_val = int(dels) if dels != "-" else 0
            current_commit["files_changed"] += 1
            current_commit["insertions"] += ins_val
            current_commit["deletions"] += dels_val
            commit_files.append({
                "commit_hash": current_commit["hash"],
                "file_path": filepath,
                "change_type": "modified",  # numstat 不区分类型，简化为 modified
            })

    if current_commit and "hash" in current_commit:
        commits.append(current_commit)

    return {"commits": commits, "commit_files": commit_files}


def load_existing_commits(context: Path) -> list[dict]:
    """读取已有 commits.jsonl。"""
    path = context / "index" / "commits.jsonl"
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return result


def append_new_commits(context: Path, commits: list[dict], commit_files: list[dict]) -> int:
    """增量追加新 commit，返回新增数量。"""
    existing = load_existing_commits(context)
    existing_hashes = {c["hash"] for c in existing}

    new_commits = [c for c in commits if c["hash"] not in existing_hashes]
    if not new_commits:
        return 0

    new_hashes = {c["hash"] for c in new_commits}
    new_files = [f for f in commit_files if f["commit_hash"] in new_hashes]

    index_dir = context / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    # 追加 commits
    with (index_dir / "commits.jsonl").open("a", encoding="utf-8") as f:
        for commit in new_commits:
            f.write(json.dumps(commit, sort_keys=True) + "\n")

    # 追加 commit_files
    with (index_dir / "commit_files.jsonl").open("a", encoding="utf-8") as f:
        for cf in new_files:
            f.write(json.dumps(cf, sort_keys=True) + "\n")

    return len(new_commits)


def is_git_stale(context: Path, root: Path) -> bool:
    """比对 commits.jsonl 最新 hash 与 HEAD。"""
    existing = load_existing_commits(context)
    if not existing:
        return True
    latest_hash = existing[-1]["hash"]
    try:
        head = _git(root, ["rev-parse", "HEAD"]).strip()
        return latest_hash != head
    except (OSError, subprocess.TimeoutExpired):
        return False
