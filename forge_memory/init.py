"""初始化 .project-context 目录。"""

from __future__ import annotations

import json
from pathlib import Path

from .utils import (
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


def initialize(root: Path, allow_empty_root: bool = False) -> list[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"项目根目录不存在：{root}")
    if not root.is_dir():
        raise NotADirectoryError(f"项目根目录不是目录：{root}")
    if not allow_empty_root and not has_project_signal(root):
        raise ValueError("未发现明显项目信号；如确认这是项目根目录，请添加 --allow-empty-root。")

    context = root / ".project-context"
    created: list[Path] = []
    for child in [context, context / "sessions"]:
        if not child.exists():
            child.mkdir(parents=True, exist_ok=True)
            created.append(child)

    timestamp = now_iso()
    project_id = stable_id("proj", str(root), root.name)

    context_json = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "project_root": str(root),
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
