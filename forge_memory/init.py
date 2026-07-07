"""初始化 .project-context 目录。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .utils import (
    branch_context_path,
    current_branch,
    generated_md,
    has_project_signal,
    now_iso,
    stable_id,
)

SCHEMA_VERSION = "forge-memory.static.v1"
GENERATOR = "forge-memory"


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def check_misuse(root: Path, allow_empty_root: bool = False) -> list[str]:
    """检测常见误用场景，返回警告信息列表。"""
    warnings = []
    root = root.resolve()

    # 检查是否是 git 项目
    if not (root / ".git").exists():
        warnings.append("[Warning] 非 git 项目：commit 历史功能将受限 → 建议先运行 git init")

    # 检查项目大小
    try:
        file_count = sum(1 for _ in root.rglob("*") if _.is_file() and not any(
            part.startswith(".") or part in {"node_modules", "__pycache__", "venv", ".venv"}
            for part in _.relative_to(root).parts
        ))
        if file_count < 10:
            warnings.append(f"[Warning] 项目太小（{file_count} 个文件）：扫描意义不大 → 建议直接阅读项目文件")
        elif file_count > 50000:
            warnings.append(f"[Warning] 项目过大（{file_count} 个文件）：扫描可能耗时较长 → 建议使用 --max-files 参数限制")
    except OSError:
        pass

    # 检查是否是临时目录
    temp_patterns = {"/tmp/", "/temp/", "temp/", "tmp/", ".cache/", ".temp/"}
    root_str = str(root).lower()
    if any(pattern in root_str for pattern in temp_patterns):
        warnings.append("[Warning] 临时目录：扫描结果可能无意义 → 建议扫描正式项目目录")

    return warnings


def initialize(root: Path, allow_empty_root: bool = False) -> list[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"项目根目录不存在：{root}")
    if not root.is_dir():
        raise NotADirectoryError(f"项目根目录不是目录：{root}")
    if not allow_empty_root and not has_project_signal(root):
        raise ValueError("未发现明显项目信号；如确认这是项目根目录，请添加 --allow-empty-root。")

    # 误用警告
    warnings = check_misuse(root, allow_empty_root)
    for warning in warnings:
        print(warning, file=sys.stderr)

    context = root / ".project-context"
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)
    created: list[Path] = []
    for child in [context, context / "sessions", branch_dir, branch_dir / "index", branch_dir / "graph", branch_dir / "scans", branch_dir / "packs"]:
        if not child.exists():
            child.mkdir(parents=True, exist_ok=True)
            created.append(child)

    timestamp = now_iso()
    project_id = stable_id("proj", str(root), root.name)

    context_json = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "project_root": str(root),
        "active_branch": branch,
        "created_at": timestamp,
        "updated_at": timestamp,
        "generator": GENERATOR,
    }

    files = {
        context / "context.json": json.dumps(context_json, indent=2) + "\n",
        context / "INDEX.md": generated_md(f"""# 项目上下文索引

项目：{root.name}
项目 ID：{project_id}
创建时间：{timestamp}

## 恢复方式

读取 `project-summary.md` 即可获得项目全貌，无需读取其他文件。

## 四状态判定

- 状态 1 初始化：项目没有 `.project-context/INDEX.md`，或用户明确要求重新扫描。
- 状态 2 总结会话摘要：用户要求保存当前会话；不重新扫描。
- 状态 3 读取会话记忆：用户要求恢复历史记忆；读取 `sessions/index.md`。
- 状态 4 读取项目结构化文件：用户只想看项目全貌；只读 `project-summary.md`。

如果用户只说"使用 forge-memory"且本文件存在，先让用户选择状态。

## 状态

已初始化。运行结构化扫描以填充项目明细：

```bash
python3 forge_memory.py scan "{root}"
```
"""),
        context / "project-summary.md": generated_md("# 项目摘要\n\n尚未扫描。\n"),
        context / "sessions" / "index.md": generated_md("# 会话摘要\n\n尚未记录会话。\n"),
    }

    for path, content in files.items():
        if write_if_missing(path, content):
            created.append(path)

    return created
