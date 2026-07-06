"""读写 index/files.jsonl、index/modules.jsonl、scans/latest.json、scans/history.jsonl。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .utils import now_iso


def read_existing_index(context: Path) -> dict[str, dict]:
    """读取已有的 index/files.jsonl，返回 {path: record} 字典。"""
    index_path = context / "index" / "files.jsonl"
    if not index_path.exists():
        return {}
    result: dict[str, dict] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            if "path" in record:
                result[record["path"]] = record
        except json.JSONDecodeError:
            continue
    return result


def write_index(root: Path, scan_result: dict) -> None:
    """写出 index/files.jsonl 和 index/modules.jsonl。"""
    index_dir = root / ".project-context" / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    # files.jsonl
    file_rows = []
    for f in scan_result["files"]:
        row = {
            "id": f["id"],
            "path": f["path"],
            "name": f["name"],
            "role": f["role"],
            "language": f["language"],
            "size_bytes": f["size_bytes"],
            "content_hash": f["content_hash"],
            "module_id": f.get("module_id", ""),
            "symbols": f.get("symbols", []),
            "imports": f.get("imports", []),
            "updated_at": f.get("updated_at", ""),
        }
        file_rows.append(row)

    (index_dir / "files.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in file_rows),
        encoding="utf-8",
    )

    # modules.jsonl
    mod_rows = []
    for module_name, module_files in scan_result["modules"].items():
        from .utils import stable_id as _sid

        mod_id = _sid("mod", module_name, module_name)
        roles = sorted({item["role"] for item in module_files})
        mod_rows.append(
            {
                "id": mod_id,
                "name": module_name,
                "root_path": module_name,
                "file_count": len(module_files),
                "roles": roles,
                "summary": f"{len(module_files)} 个文件；角色：{', '.join(roles)}。",
            }
        )

    (index_dir / "modules.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in mod_rows),
        encoding="utf-8",
    )


def write_scan_summary(root: Path, scan_result: dict) -> None:
    """写出 scans/latest.json 和追加 scans/history.jsonl。"""
    scans_dir = root / ".project-context" / "scans"
    scans_dir.mkdir(parents=True, exist_ok=True)

    # 生成 scan_id
    scan_seed = f"{scan_result['scanned_at']}:{scan_result['project_id']}"
    scan_id = f"scan-{scan_result['scanned_at'][:10].replace('-', '')}-{hashlib.sha1(scan_seed.encode()).hexdigest()[:6]}"

    summary = {
        "scan_id": scan_id,
        "started_at": scan_result["scanned_at"],
        "finished_at": now_iso(),
        "status": "success",
        "file_count": len(scan_result["files"]),
        "module_count": len(scan_result["modules"]),
        "changed_files": scan_result.get("changed_files", 0),
        "unchanged_files": scan_result.get("unchanged_files", 0),
        "new_files": scan_result.get("new_files", 0),
        "deleted_files": scan_result.get("deleted_files", 0),
        "errors": [],
    }

    # latest.json
    (scans_dir / "latest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # history.jsonl — 追加
    with (scans_dir / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary, sort_keys=True) + "\n")
