#!/usr/bin/env python3
"""Forge Memory — 面向研发智能体的本地项目记忆层 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forge_memory.context_pack import generate_context_pack
from forge_memory.doctor import doctor as cmd_doctor_impl
from forge_memory.git_history import append_new_commits, is_git_stale, scan_git_history
from forge_memory.grapher import write_graph
from forge_memory.impact import analyze_impact, format_impact
from forge_memory.sqlite_backend import import_jsonl_to_sqlite
from forge_memory.indexer import read_existing_index, write_index, write_scan_summary
from forge_memory.init import initialize
from forge_memory.quickstart import quickstart as cmd_quickstart_impl
from forge_memory.renderer import render_full_summary
from forge_memory.scanner import migrate_to_branch_structure, scan
from forge_memory.session import add_session, list_sessions
from forge_memory.status import get_status
from forge_memory.utils import branch_context_path, current_branch


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


# --- 噪声置信度排查 ---

# 已知噪声目录模式（后缀或全名匹配）
_NOISE_PATTERNS = {
    "cache", "temp", "tmp", "output", "generated", "artifacts",
    "coverage", "logs", "log", "snapshots", ".gradle", ".cxx",
}

# 标准项目结构目录（不算噪声）
_STANDARD_DIRS = {
    "src", "lib", "app", "test", "tests", "spec", "specs",
    "docs", "doc", "scripts", "bin", "cmd", "pkg", "internal",
    "api", "config", "conf", "public", "static", "assets",
    "resources", "res", "tools", "utils", "util", "common",
    "shared", "core", "models", "views", "controllers", "routes",
    "services", "handlers", "middleware", "plugins", "modules",
    "components", "pages", "layouts", "styles", "css", "scss",
    "fonts", "images", "img", "icons", "locales", "i18n",
    "migrations", "seeds", "fixtures", "mocks", "stubs",
    "android", "ios", "ohos", "linux", "windows", "macos", "web",
}


def _check_noise(root: Path, result: dict) -> None:
    """初始化扫描后，检测可能的噪声目录并输出警告。"""
    from collections import Counter

    # 统计每个顶层目录的文件数
    top_dir_counts: Counter[str] = Counter()
    for f in result["files"]:
        parts = f["path"].split("/")
        if len(parts) > 1:
            top_dir_counts[parts[0]] += 1

    total_files = len(result["files"])
    if total_files == 0:
        return

    # 识别可能的噪声目录
    suspects: list[tuple[str, int, str]] = []  # (dir, count, reason)
    for d, count in top_dir_counts.items():
        d_lower = d.lower()
        # 已知噪声模式
        if d_lower in _NOISE_PATTERNS or any(
            d_lower.endswith(s) for s in _NOISE_PATTERNS
        ):
            suspects.append((d, count, "匹配已知噪声模式"))
        # 非标准目录且文件数占比超过 15%
        elif d not in _STANDARD_DIRS and count / total_files > 0.15:
            suspects.append((d, count, f"非常规目录，占文件总数 {count / total_files:.0%}"))

    if not suspects:
        return

    # 计算置信度
    suspect_files = sum(c for _, c, _ in suspects)
    ratio = suspect_files / total_files
    if ratio > 0.5:
        confidence = "高"
    elif ratio > 0.3:
        confidence = "中"
    else:
        confidence = "低"

    print("\n--- 噪声置信度排查 ---")
    print(f"置信度：{confidence}（疑似噪声文件 {suspect_files}/{total_files}）")
    for d, count, reason in suspects:
        print(f"  {d}/  —  {count} 个文件，原因：{reason}")
    print()
    print("提示：这些目录可能包含缓存、构建产物或依赖，不影响核心代码理解。")
    print(f"如需排除，请将目录名添加到 {root / '.forgeignore'} 或在扫描后手动清理 project-summary.md。")


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

    # 迁移旧结构到分支子目录
    branch = migrate_to_branch_structure(root)
    branch_dir = branch_context_path(root, branch)

    # 降级策略：备份当前索引，扫描失败时回滚
    backup_dir = branch_dir / ".backup"
    index_dir = branch_dir / "index"
    if index_dir.exists() and any(index_dir.iterdir()):
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(index_dir, backup_dir)
        except OSError as e:
            print(f"警告：无法备份索引：{e}", file=sys.stderr)

    # 读取已有索引用于增量扫描
    existing_index = read_existing_index(branch_dir) if not args.force else {}

    try:
        result = scan(root, args.max_file_bytes, existing_index)
    except Exception as e:
        # 扫描失败，回滚到备份
        print(f"[ScanError] 扫描中途失败：{e} → 正在回滚到上一次成功状态...", file=sys.stderr)
        if backup_dir.exists():
            try:
                if index_dir.exists():
                    shutil.rmtree(index_dir)
                shutil.copytree(backup_dir, index_dir)
                print("已回滚到上一次成功的索引状态。", file=sys.stderr)
                print(f"恢复命令：python3 forge_memory.py scan {root}", file=sys.stderr)
            except OSError as rollback_err:
                print(f"[ScanError] 回滚失败：{rollback_err} → 请手动恢复或重新扫描", file=sys.stderr)
        else:
            print(f"[ScanError] 无备份可回滚 → 请运行 python3 forge_memory.py scan {root} 重新扫描", file=sys.stderr)
        return 1

    write_index(root, result, branch_dir)
    write_scan_summary(root, result, branch_dir)
    write_graph(root, result, branch_dir)

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
        ctx["active_branch"] = branch
        ctx_path.write_text(json.dumps(ctx, indent=2) + "\n", encoding="utf-8")

    # Git 历史扫描
    git_result = scan_git_history(root)
    new_commits = append_new_commits(branch_dir, git_result["commits"], git_result["commit_files"])

    # 清理备份
    if backup_dir.exists():
        try:
            shutil.rmtree(backup_dir)
        except OSError:
            pass

    # 初始化扫描时，执行噪声置信度排查
    is_init_scan = existing_index == {}
    if is_init_scan:
        _check_noise(root, result)

    print(f"已扫描项目：{root}")
    print(f"当前分支：{branch}")
    print(f"索引目录：{branch_dir}")
    print(f"已索引文件：{len(result['files'])}")
    print(f"已索引模块：{len(result['modules'])}")
    print(f"图谱节点：{len(result['nodes'])}")
    print(f"图谱关系：{len(result['edges'])}")
    print(f"变更文件：{result['changed_files']}，未变：{result['unchanged_files']}，新增：{result['new_files']}，删除：{result['deleted_files']}")
    print(f"Git commit：{len(git_result['commits'])} 个（新增 {new_commits}）")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    status = get_status(root)
    if status.get("status") == "未扫描":
        print(f"项目：{status['project_name']}")
        print(f"分支：{status['branch']}")
        print(f"状态：{status['message']}")
        return 0
    print(f"项目：{status['project_name']}")
    print(f"分支：{status['branch']}")
    print(f"状态：{status['status']}")
    print(f"最后扫描：{status['last_scan']}")
    print(f"扫描 ID：{status['scan_id']}")
    print(f"文件总数：{status['file_count']}")
    print(f"模块总数：{status['module_count']}")
    print(f"变更文件：{status['changed_files']}")
    print(f"未变文件：{status['unchanged_files']}")
    print(f"新增文件：{status['new_files']}")
    print(f"删除文件：{status['deleted_files']}")
    print(f"Commit 数：{status.get('commit_count', 0)}")

    # 显示健康度指标
    health = status.get("health", {})
    if health:
        print("\n索引健康度：")
        print(f"  文件覆盖率：{health.get('file_coverage', 'N/A')} ({health.get('file_coverage_status', 'unknown')})")
        print(f"  索引新鲜度：{health.get('index_freshness', 'unknown')} ({health.get('index_age_hours', 'N/A')} 小时)")
        print(f"  Hash 覆盖率：{health.get('hash_coverage', 'N/A')}")

    # 质量评分
    grade = status.get("quality_grade", "")
    if grade:
        print(f"\n质量评分：{grade}")
    advice = status.get("rescan_advice", "")
    if advice:
        print(f"建议：{advice}")

    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)
    entry_files = args.entry if args.entry else None
    pack = generate_context_pack(root, args.task, entry_files)

    packs_dir = branch_dir / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    pack_path = packs_dir / "latest-context-pack.md"
    pack_path.write_text(pack, encoding="utf-8")

    print(f"已生成上下文包：{pack_path}")
    print(pack)
    return 0


def cmd_import_db(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    branch = args.branch or current_branch(root)
    context = root / ".project-context"
    branch_dir = branch_context_path(root, branch)

    if not (branch_dir / "index" / "files.jsonl").exists():
        print(f"错误：未找到分支 {branch} 的索引，请先运行 scan。", file=sys.stderr)
        return 1

    db_path, counts = import_jsonl_to_sqlite(branch_dir, branch)
    print(f"已导入 SQLite：{db_path}")
    for table, count in counts.items():
        print(f"  {table}: {count} 行")
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    branch = current_branch(root)
    branch_dir = branch_context_path(root, branch)

    if not (branch_dir / "index" / "files.jsonl").exists():
        print(f"错误：未找到分支 {branch} 的索引，请先运行 scan。", file=sys.stderr)
        return 1

    # 过期检测：自动更新 git 历史
    if is_git_stale(branch_dir, root):
        print(f"检测到新 commit，自动更新 git 历史...")
        git_result = scan_git_history(root)
        new_commits = append_new_commits(branch_dir, git_result["commits"], git_result["commit_files"])
        print(f"已更新：{new_commits} 个新 commit")

    result = analyze_impact(root, args.file_path, branch_dir)
    print(format_impact(result))
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


def cmd_quickstart(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    return cmd_quickstart_impl(root, interactive=True)


def cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    return cmd_doctor_impl(root)


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

    # impact
    p_impact = subparsers.add_parser("impact", help="文件影响分析")
    p_impact.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_impact.add_argument("file_path", help="要分析的文件路径")

    # import-db
    p_import_db = subparsers.add_parser("import-db", help="导入 JSONL 到 SQLite")
    p_import_db.add_argument("project_root", nargs="?", default=".", help="项目根目录")
    p_import_db.add_argument("--branch", help="指定分支（默认当前分支）")

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

    # quickstart
    p_quickstart = subparsers.add_parser("quickstart", help="一键初始化（init + scan + 上下文包）")
    p_quickstart.add_argument("project_root", nargs="?", default=".", help="项目根目录")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="检查环境依赖和索引健康状态")
    p_doctor.add_argument("project_root", nargs="?", default=".", help="项目根目录")

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
    elif args.command == "impact":
        return cmd_impact(args)
    elif args.command == "import-db":
        return cmd_import_db(args)
    elif args.command == "session":
        if args.session_command == "add":
            return cmd_session_add(args)
        elif args.session_command == "list":
            return cmd_session_list(args)
        else:
            p_session.print_help()
            return 1
    elif args.command == "quickstart":
        return cmd_quickstart(args)
    elif args.command == "doctor":
        return cmd_doctor(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
