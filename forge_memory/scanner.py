"""文件遍历、分类、hash、符号/导入提取。迁移自 project-memory scan_project.py。"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import sys

from .utils import (
    CONFIG_NAMES,
    DOC_PATTERNS,
    EXCLUDE_DIRS,
    EXCLUDE_SUFFIXES,
    IMPORT_PATTERNS,
    LANG_BY_SUFFIX,
    ROLE_LABELS,
    SYMBOL_PATTERNS,
    branch_context_path,
    content_hash,
    current_branch,
    format_error,
    is_text_file,
    now_iso,
    read_text,
    rel,
    slugify,
    stable_id,
)

# 大项目分批扫描参数
MAX_BATCH_SIZE = 1000
MAX_BATCH_BYTES = 10 * 1024 * 1024  # 10MB


def save_scan_progress(branch_dir: Path, progress: dict) -> None:
    """保存扫描进度到 .project-context/scan-progress.json"""
    progress_path = branch_dir / "scan-progress.json"
    try:
        progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass


def load_scan_progress(branch_dir: Path) -> dict | None:
    """加载扫描进度，如果不存在或无效则返回 None"""
    progress_path = branch_dir / "scan-progress.json"
    if not progress_path.exists():
        return None
    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "completed_files" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def clear_scan_progress(branch_dir: Path) -> None:
    """清理扫描进度文件"""
    progress_path = branch_dir / "scan-progress.json"
    try:
        if progress_path.exists():
            progress_path.unlink()
    except OSError:
        pass


def migrate_to_branch_structure(root: Path) -> str:
    """检测旧结构并迁移到 branches/<branch>/。返回当前分支名。"""
    context = root / ".project-context"
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)

    # 检查旧结构是否存在
    old_index = context / "index"
    old_graph = context / "graph"
    old_scans = context / "scans"
    old_packs = context / "packs"

    if not old_index.exists() and not old_graph.exists() and not old_scans.exists():
        # 无旧结构，确保分支目录存在
        for subdir in ["index", "graph", "scans", "packs"]:
            (branch_dir / subdir).mkdir(parents=True, exist_ok=True)
        return branch

    # 迁移旧结构到分支目录
    branch_dir.mkdir(parents=True, exist_ok=True)
    for old_dir, subdir in [(old_index, "index"), (old_graph, "graph"), (old_scans, "scans"), (old_packs, "packs")]:
        if old_dir.exists():
            target = branch_dir / subdir
            if target.exists():
                # 合并：移动旧文件到分支目录（不覆盖已有）
                for item in old_dir.iterdir():
                    dest = target / item.name
                    if not dest.exists():
                        shutil.move(str(item), str(dest))
                old_dir.rmdir()
            else:
                shutil.move(str(old_dir), str(target))

    # 更新 context.json
    ctx_path = context / "context.json"
    if ctx_path.exists():
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        ctx["active_branch"] = branch
        ctx_path.write_text(json.dumps(ctx, indent=2) + "\n", encoding="utf-8")

    return branch


def classify_file(path: Path) -> str:
    name = path.name
    if name in CONFIG_NAMES or name.startswith(".env.example"):
        return "config"
    if path.suffix.lower() in {".md", ".rst", ".txt"} or DOC_PATTERNS.search(name):
        return "document"
    if "test" in path.parts or "tests" in path.parts or path.name.endswith(
        ("_test.py", ".test.ts", ".spec.ts")
    ):
        return "test"
    if path.suffix.lower() in LANG_BY_SUFFIX:
        return "source"
    return "other"


def module_key(relative_path: str) -> str:
    parts = relative_path.split("/")
    if len(parts) == 1:
        return "."
    if parts[0] in {
        "src", "lib", "app", "packages", "apps", "services", "backend", "frontend",
    } and len(parts) > 2:
        return "/".join(parts[:2])
    return parts[0]


def git_lines(root: Path, args: list[str]) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    return [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]


def scan_worktree(root: Path) -> dict:
    branch = git_lines(root, ["branch", "--show-current"])
    status = git_lines(root, ["status", "--short"])
    return {
        "is_git_repo": bool(
            branch or status or git_lines(root, ["rev-parse", "--git-dir"])
        ),
        "branch": branch[0] if branch else "",
        "status": status,
    }


def extract_symbols(text: str) -> list[str]:
    names: list[str] = []
    for pattern in SYMBOL_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(1)
            if name not in names:
                names.append(name)
            if len(names) >= 20:
                return names
    return names


def extract_imports(text: str) -> list[str]:
    imports: list[str] = []
    for pattern in IMPORT_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1)
            if value and value not in imports:
                imports.append(value)
            if len(imports) >= 30:
                return imports
    return imports


def extract_first_paragraph(text: str) -> str:
    lines = text.splitlines()
    paragraph_lines = []
    in_paragraph = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---" and not in_paragraph:
            continue
        if stripped.startswith("#") and not in_paragraph:
            in_paragraph = True
            continue
        if in_paragraph and (stripped.startswith("#") or stripped == ""):
            break
        if in_paragraph and stripped:
            paragraph_lines.append(stripped)
    return " ".join(paragraph_lines)[:700].rstrip() if paragraph_lines else ""


def extract_code_comments(text: str, language: str) -> str:
    lines = text.splitlines()
    comments = []
    for i, line in enumerate(lines[:50]):
        stripped = line.strip()
        if language == "python" and stripped.startswith(('"""', "'''")):
            quote = '"""' if stripped.startswith('"""') else "'''"
            comment = stripped.lstrip(quote).rstrip(quote).strip()
            if comment:
                comments.append(comment)
            if not stripped.endswith(quote) or stripped.count(quote) < 2:
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if quote in next_line:
                        end_comment = next_line.split(quote)[0].strip()
                        if end_comment:
                            comments.append(end_comment)
                        break
                    if next_line:
                        comments.append(next_line)
            break
        elif language in ("javascript", "typescript") and stripped.startswith("/**"):
            comment = stripped.lstrip("/**").rstrip("*/").strip()
            if comment:
                comments.append(comment)
            if not stripped.endswith("*/"):
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if "*/" in next_line:
                        end_comment = next_line.split("*/")[0].strip().lstrip("* ")
                        if end_comment:
                            comments.append(end_comment)
                        break
                    if next_line and not next_line.startswith("*"):
                        comments.append(next_line.lstrip("* ").strip())
            break
        elif stripped.startswith(("#", "//", "--")) and not stripped.startswith(
            ("#!", "//=", "--=")
        ):
            comment = stripped.lstrip("#/ -").strip()
            if comment and len(comment) > 10:
                comments.append(comment)
                break
    return " ".join(comments)[:300].rstrip() if comments else ""


def extract_package_scripts(text: str) -> list[str]:
    import json

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []
    return [
        f"{name}: {value}"
        for name, value in sorted(scripts.items())
        if isinstance(value, str)
    ]


def extract_package_dependencies(text: str) -> list[str]:
    import json

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    for key in [
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ]:
        deps = data.get(key)
        if isinstance(deps, dict):
            for name in deps:
                if name not in names:
                    names.append(name)
    return sorted(names)


def dedupe_nodes(nodes: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for node in nodes:
        seen.setdefault(node["id"], node)
    return list(seen.values())


def dedupe_edges(edges: list[dict]) -> list[dict]:
    seen: dict[tuple, dict] = {}
    for edge in edges:
        key = (edge["from"], edge["to"], edge["type"])
        seen.setdefault(key, edge)
    return list(seen.values())


def scan(
    root: Path,
    max_file_bytes: int = 200_000,
    existing_index: dict[str, dict] | None = None,
) -> dict:
    """扫描项目，返回结构化结果。

    Args:
        root: 项目根目录
        max_file_bytes: 每个文件最多读取的字节数
        existing_index: 已有的 index/files.jsonl 数据，格式为 {path: record}，
                        用于增量扫描（content_hash 一致时复用原记录）

    Returns:
        dict 含 files, modules, nodes, edges, worktree,
              changed_files, unchanged_files, new_files, deleted_files
    """
    root = root.resolve()
    if existing_index is None:
        existing_index = {}

    files: list[dict] = []
    modules: dict[str, list[dict]] = defaultdict(list)
    nodes: list[dict] = []
    edges: list[dict] = []
    project_id = stable_id("proj", str(root), root.name)
    timestamp = now_iso()

    nodes.append(
        {
            "id": project_id,
            "type": "project",
            "name": root.name,
            "path": ".",
            "summary": "项目根目录。",
            "meta": {"scanned_at": timestamp},
        }
    )

    changed_files = 0
    unchanged_files = 0
    new_files = 0
    seen_paths: set[str] = set()

    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = sorted(
            d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".tmp")
        )
        filenames = sorted(filenames)

        if current_path == root:
            current_rel = "."
        else:
            current_rel = rel(current_path, root)
            dir_id = stable_id("dir", current_rel, current_path.name)
            nodes.append(
                {
                    "id": dir_id,
                    "type": "directory",
                    "name": current_path.name,
                    "path": current_rel,
                    "summary": "项目目录。",
                    "meta": {},
                }
            )
            edges.append(
                {
                    "from": project_id,
                    "to": dir_id,
                    "type": "contains",
                    "summary": "项目包含目录。",
                    "meta": {},
                }
            )

        for filename in filenames:
            path = current_path / filename
            if (
                path.suffix.lower() in EXCLUDE_SUFFIXES
                or not is_text_file(path, max_file_bytes)
            ):
                continue

            relative = rel(path, root)
            seen_paths.add(relative)
            role = classify_file(path)
            language = LANG_BY_SUFFIX.get(path.suffix.lower(), "")
            size = path.stat().st_size

            # 读取文件内容并计算 content_hash
            raw_bytes = path.read_bytes()[:max_file_bytes]
            file_hash = content_hash(raw_bytes)
            text = raw_bytes.decode("utf-8", errors="replace")

            symbols = extract_symbols(text) if role in {"source", "test"} else []
            imports = extract_imports(text) if role in {"source", "test", "config"} else []

            first_heading = ""
            excerpt = ""
            code_comment = ""
            commands: list[str] = []
            dependencies: list[str] = []

            if role == "document":
                for line in text.splitlines():
                    if line.strip().startswith("#"):
                        first_heading = line.strip("# ").strip()
                        break
                excerpt = extract_first_paragraph(text)
            elif role == "source":
                code_comment = extract_code_comments(text, language)
            if path.name == "package.json":
                commands = extract_package_scripts(text)
                dependencies = extract_package_dependencies(text)

            file_id = stable_id("file", relative, path.name)
            module_id = stable_id("mod", module_key(relative), module_key(relative))

            # 增量判断
            change_status = "new"
            if relative in existing_index:
                old_record = existing_index[relative]
                if old_record.get("content_hash") == file_hash:
                    change_status = "unchanged"
                    unchanged_files += 1
                else:
                    change_status = "changed"
                    changed_files += 1
            else:
                new_files += 1

            record = {
                "id": file_id,
                "path": relative,
                "name": path.name,
                "role": role,
                "language": language,
                "size_bytes": size,
                "content_hash": file_hash,
                "module_id": module_id,
                "module": module_key(relative),
                "symbols": symbols,
                "imports": imports,
                "heading": first_heading,
                "excerpt": excerpt,
                "code_comment": code_comment,
                "commands": commands,
                "dependencies": dependencies,
                "change_status": change_status,
                "updated_at": timestamp,
            }
            files.append(record)
            modules[record["module"]].append(record)

            node_type = (
                "config" if role == "config"
                else "document" if role == "document"
                else "file"
            )
            summary_bits = [role]
            if language:
                summary_bits.append(language)
            if first_heading:
                summary_bits.append(first_heading)
            elif code_comment:
                summary_bits.append(code_comment[:100])

            nodes.append(
                {
                    "id": file_id,
                    "type": node_type,
                    "name": path.name,
                    "path": relative,
                    "summary": "; ".join(summary_bits),
                    "meta": {
                        "language": language,
                        "size_bytes": size,
                        "role": role,
                    },
                }
            )

            parent_key = current_rel if current_rel != "." else "."
            parent_id = (
                project_id
                if parent_key == "."
                else stable_id("dir", parent_key, Path(parent_key).name)
            )
            edges.append(
                {
                    "from": parent_id,
                    "to": file_id,
                    "type": "contains",
                    "summary": "目录包含文件。",
                    "meta": {},
                }
            )

            for symbol in symbols:
                symbol_id = stable_id("sym", f"{relative}::{symbol}", symbol)
                nodes.append(
                    {
                        "id": symbol_id,
                        "type": "symbol",
                        "name": symbol,
                        "path": relative,
                        "summary": f"符号定义于 {relative}。",
                        "meta": {"file_id": file_id},
                    }
                )
                edges.append(
                    {
                        "from": file_id,
                        "to": symbol_id,
                        "type": "defines",
                        "summary": "文件定义符号。",
                        "meta": {},
                    }
                )

            for imported in imports:
                import_id = stable_id("mod", imported, imported.split("/")[-1])
                nodes.append(
                    {
                        "id": import_id,
                        "type": "module",
                        "name": imported,
                        "path": "",
                        "summary": "导入的模块或包。",
                        "meta": {"external_or_unresolved": True},
                    }
                )
                edges.append(
                    {
                        "from": file_id,
                        "to": import_id,
                        "type": "imports",
                        "summary": "文件导入模块。",
                        "meta": {},
                    }
                )

    # 计算已删除文件
    deleted_files = 0
    for old_path in existing_index:
        if old_path not in seen_paths:
            deleted_files += 1

    # 生成模块节点和边
    for module, module_files in sorted(modules.items()):
        mod_id = stable_id("mod", module, module)
        roles = sorted({item["role"] for item in module_files})
        nodes.append(
            {
                "id": mod_id,
                "type": "module",
                "name": module,
                "path": module,
                "summary": f"{len(module_files)} 个文件；角色：{', '.join(roles)}。",
                "meta": {"file_count": len(module_files), "roles": roles},
            }
        )
        edges.append(
            {
                "from": project_id,
                "to": mod_id,
                "type": "contains",
                "summary": "项目包含模块。",
                "meta": {},
            }
        )
        for item in module_files:
            edges.append(
                {
                    "from": mod_id,
                    "to": item["id"],
                    "type": "contains",
                    "summary": "模块包含文件。",
                    "meta": {},
                }
            )

    return {
        "root": str(root),
        "project_id": project_id,
        "scanned_at": timestamp,
        "files": sorted(files, key=lambda x: x["path"]),
        "modules": {
            key: sorted(value, key=lambda x: x["path"])
            for key, value in sorted(modules.items())
        },
        "nodes": dedupe_nodes(nodes),
        "edges": dedupe_edges(edges),
        "worktree": scan_worktree(root),
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
        "new_files": new_files,
        "deleted_files": deleted_files,
    }
