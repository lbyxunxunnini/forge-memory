"""一键初始化：init + scan + 生成示例上下文包。"""

from __future__ import annotations

import sys
from pathlib import Path

from .context_pack import generate_context_pack
from .init import check_misuse, initialize
from .scanner import migrate_to_branch_structure, scan
from .indexer import write_index, write_scan_summary
from .grapher import write_graph
from .renderer import render_full_summary
from .utils import branch_context_path, generated_md


def quickstart(root: Path, interactive: bool = True) -> int:
    """一键初始化项目记忆。

    Args:
        root: 项目根目录
        interactive: 是否交互式（显示提示）

    Returns:
        0 成功，1 失败
    """
    root = root.resolve()

    # 1. 检查是否已有索引
    context = root / ".project-context"
    if (context / "context.json").exists():
        if interactive:
            print("已存在索引，跳过初始化。")
            print(f"如需重新扫描，请运行：python3 forge_memory.py scan {root}")
            return 0
        else:
            print("已存在索引，跳过扫描。")
            return 0

    # 2. 误用警告
    warnings = check_misuse(root)
    for warning in warnings:
        print(warning, file=sys.stderr)

    # 3. 初始化
    try:
        created = initialize(root, allow_empty_root=True)
        print("✓ 初始化完成")
    except Exception as e:
        print(f"✗ 初始化失败：{e}", file=sys.stderr)
        return 1

    # 4. 扫描
    try:
        branch = migrate_to_branch_structure(root)
        branch_dir = branch_context_path(root, branch)
        result = scan(root)
        write_index(root, result, branch_dir)
        write_scan_summary(root, result, branch_dir)
        write_graph(root, result, branch_dir)
        print("✓ 扫描完成")
    except Exception as e:
        print(f"✗ 扫描失败：{e}", file=sys.stderr)
        return 1

    # 5. 生成示例上下文包
    try:
        context_content = generate_context_pack(root, "项目概览")
        packs_dir = branch_dir / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        (packs_dir / "latest-context-pack.md").write_text(context_content, encoding="utf-8")
        print("✓ 上下文包生成完成")
    except Exception as e:
        print(f"✗ 上下文包生成失败：{e}", file=sys.stderr)
        return 1

    # 6. 写入 project-summary.md
    try:
        summary_content = generated_md(render_full_summary(result))
        (context / "project-summary.md").write_text(summary_content, encoding="utf-8")
    except Exception:
        pass

    # 7. 输出使用提示
    print("\n快速开始：")
    print(f"  python3 forge_memory.py status {root}")
    print(f"  python3 forge_memory.py context {root} --task '你的任务'")

    return 0
