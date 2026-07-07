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
from .utils import branch_context_path, generated_md, ForgeMemoryError, ScanError, ContextError


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
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"[InitError] 初始化失败：{e} → 请检查项目目录是否存在且有效", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"[InitError] 初始化失败（文件系统错误）：{e} → 请检查目录权限", file=sys.stderr)
        return 1

    # 4. 扫描
    try:
        branch = migrate_to_branch_structure(root)
        branch_dir = branch_context_path(root, branch)
        result = scan(root, branch_dir=branch_dir)
        write_index(root, result, branch_dir)
        write_scan_summary(root, result, branch_dir)
        write_graph(root, result, branch_dir)
        print("✓ 扫描完成")
    except ScanError as e:
        print(f"✗ 扫描失败：{e} → 请检查项目目录是否过大或包含不可读文件", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"[ScanError] 扫描失败（文件系统错误）：{e} → 请检查磁盘空间和文件权限", file=sys.stderr)
        return 1

    # 5. 生成示例上下文包
    try:
        context_content = generate_context_pack(root, "项目概览")
        packs_dir = branch_dir / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        (packs_dir / "latest-context-pack.md").write_text(context_content, encoding="utf-8")
        print("✓ 上下文包生成完成")
    except (FileNotFoundError, ValueError) as e:
        print(f"[ContextError] 上下文包生成失败：{e} → 索引可能不完整，请重新运行 scan", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"[ContextError] 上下文包生成失败（文件写入错误）：{e} → 请检查磁盘空间", file=sys.stderr)
        return 1

    # 6. 写入 project-summary.md
    try:
        summary_content = generated_md(render_full_summary(result))
        (context / "project-summary.md").write_text(summary_content, encoding="utf-8")
    except OSError as e:
        print(f"[QuickstartError] project-summary.md 写入失败：{e} → 不影响核心功能，可手动运行 scan 更新", file=sys.stderr)

    # 7. 输出渐进式引导
    print("\n入门完成 ✓  推荐学习路径：")
    print(f"  ① 查看索引状态：")
    print(f"     python3 forge_memory.py status {root}")
    print(f"  ② 生成任务上下文包（按任务描述匹配相关文件）：")
    print(f"     python3 forge_memory.py context {root} --task '你的任务描述'")
    print(f"  ③ 分析文件影响范围（修改前评估波及面）：")
    print(f"     python3 forge_memory.py impact {root} <file-path>")
    print(f"\n进阶用法：")
    print(f"  - 增量扫描：再次 scan 自动基于 content_hash 只处理变更文件")
    print(f"  - 分支隔离：切换 git 分支后索引自动隔离到 branches/<分支名>/")
    print(f"  - 会话记忆：开发完成后保存会话摘要，下次回来能接上")
    print(f"     python3 forge_memory.py session add {root} --title '会话标题'")

    return 0
