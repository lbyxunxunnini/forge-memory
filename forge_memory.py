#!/usr/bin/env python3
"""Forge Memory — 面向研发智能体的本地项目记忆层 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forge_memory.context_pack import generate_context_pack
from forge_memory.grapher import write_graph
from forge_memory.indexer import read_existing_index, write_index, write_scan_summary
from forge_memory.init import initialize
from forge_memory.renderer import render_full_summary
from forge_memory.scanner import scan
from forge_memory.session import add_session, list_sessions
from forge_memory.status import get_status


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    try:
        created = initialize(root, allow_empty_root=args.allow_empty_root)
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    print(f"已初始化项目上下文：{root / '.project-context'}")
    if created:
        print("已创建：")
        for path in created:
            print(f"- {path}")
    else:
        print("未创建新文件；上下文目录已存在。")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    context = root / ".project-context"

    # 自动初始化（检查 context.json 是否存在，而非仅检查目录）
    if not (context / "context.json").exists():
        print("未发现 .project-context/context.json，自动初始化...")
        try:
            initialize(root, allow_empty_root=True)
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            print(f"错误：{e}", file=sys.stderr)
            return 1

    # 读取已有索引用于增量扫描
    existing_index = read_existing_index(context) if not args.force else {}

    result = scan(root, args.max_file_bytes, existing_index)
    write_index(root, result)
    write_scan_summary(root, result)
    write_graph(root, result)

    # 写入 project-summary.md
    from forge_memory.utils import generated_md, safe_to_overwrite

    summary_path = context / "project-summary.md"
    summary_content = generated_md(render_full_summary(result))
    if not safe_to_overwrite(summary_path) and not args.force:
        print(f"警告：{summary_path} 可能含人工内容，使用 --force 覆盖。")
    else:
        summary_path.write_text(summary_content, encoding="utf-8")

    # 更新 context.json
    ctx_path = context / "context.json"
    if ctx_path.exists():
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        ctx["updated_at"] = result["scanned_at"]
        ctx_path.write_text(json.dumps(ctx, indent=2) + "\n", encoding="utf-8")

    print(f"已扫描项目：{root}")
    print(f"已索引文件：{len(result['files'])}")
    print(f"已索引模块：{len(result['modules'])}")
    print(f"图谱节点：{len(result['nodes'])}")
    print(f"图谱关系：{len(result['edges'])}")
    print(f"变更文件：{result['changed_files']}，未变：{result['unchanged_files']}，新增：{result['new_files']}，删除：{result['deleted_files']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    status = get_status(root)
    if status.get("status") == "未扫描":
        print(f"项目：{status['project_name']}")
        print(f"状态：{status['message']}")
        return 0
    print(f"项目：{status['project_name']}")
    print(f"状态：{status['status']}")
    print(f"最后扫描：{status['last_scan']}")
    print(f"扫描 ID：{status['scan_id']}")
    print(f"文件总数：{status['file_count']}")
    print(f"模块总数：{status['module_count']}")
    print(f"变更文件：{status['changed_files']}")
    print(f"未变文件：{status['unchanged_files']}")
    print(f"新增文件：{status['new_files']}")
    print(f"删除文件：{status['deleted_files']}")
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    entry_files = args.entry if args.entry else None
    pack = generate_context_pack(root, args.task, entry_files)

    packs_dir = root / ".project-context" / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_path = packs_dir / "latest-context-pack.md"
    pack_path.write_text(pack, encoding="utf-8")

    print(f"已生成上下文包：{pack_path}")
    print(pack)
    return 0


def cmd_session_add(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()

    if args.from_file:
        body = Path(args.from_file).read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()

    try:
        session_id = add_session(root, args.title, body, args.allow_incomplete)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    print(f"已添加会话摘要。会话 ID：{session_id}")
    return 0


def cmd_session_list(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    try:
        sessions = list_sessions(root)
    except FileNotFoundError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(sessions, indent=2, ensure_ascii=False))
        return 0

    if not sessions:
        print("未找到会话摘要。")
        return 0

    for i, item in enumerate(sessions, 1):
        print(f"{i}. {item['date']} {item['id']} - {item['title']}")
        print(f"   {item['path']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="forge-memory",
        description="Forge Memory — 面向研发智能体的本地项目记忆层。",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init
    p_init = subparsers.add_parser("init", help="初始化 .project-context 目录")
    p_init.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_init.add_argument("--allow-empty-root", action="store_true", help="允许在空目录中初始化")

    # scan
    p_scan = subparsers.add_parser("scan", help="扫描项目并生成索引")
    p_scan.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_scan.add_argument("--max-file-bytes", type=int, default=200_000, help="每个文件最多读取的字节数")
    p_scan.add_argument("--force", action="store_true", help="强制全量重新扫描")
    p_scan.add_argument("--backup", action="store_true", help="覆盖前备份已有文件")

    # status
    p_status = subparsers.add_parser("status", help="查看扫描状态")
    p_status.add_argument("project_root", nargs="?", default=".", help="项目根目录")

    # context
    p_context = subparsers.add_parser("context", help="生成任务级上下文包")
    p_context.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_context.add_argument("--task", required=True, help="任务描述")
    p_context.add_argument("--entry", nargs="*", help="入口文件路径")

    # session
    p_session = subparsers.add_parser("session", help="会话记忆管理")
    session_sub = p_session.add_subparsers(dest="session_command", help="会话子命令")

    # session add
    p_add = session_sub.add_parser("add", help="添加会话摘要")
    p_add.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_add.add_argument("--title", required=True, help="会话标题")
    p_add.add_argument("--from-file", help="从文件读取摘要正文")
    p_add.add_argument("--allow-incomplete", action="store_true", help="允许不完整摘要")

    # session list
    p_list = session_sub.add_parser("list", help="列出会话摘要")
    p_list.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_list.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "scan":
        return cmd_scan(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "context":
        return cmd_context(args)
    elif args.command == "session":
        if args.session_command == "add":
            return cmd_session_add(args)
        elif args.session_command == "list":
            return cmd_session_list(args)
        else:
            p_session.print_help()
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
