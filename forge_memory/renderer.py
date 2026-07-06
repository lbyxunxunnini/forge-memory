"""Markdown 摘要渲染。迁移自 project-memory scan_project.py render_* 函数。"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .utils import ROLE_LABELS, stable_id


# --- 辅助函数 ---


def role_counts(files: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for item in files:
        counts[item["role"]] += 1
    return dict(sorted(counts.items()))


def technology_signals(files: list[dict]) -> list[str]:
    signals: list[str] = []
    config_paths = {item["path"] for item in files if item["role"] == "config"}
    suffix_langs = sorted({item["language"] for item in files if item["language"]})
    if suffix_langs:
        signals.append("语言/文件类型：" + "、".join(suffix_langs))
    for path, label in [
        ("package.json", "Node.js / JavaScript 生态"),
        ("tsconfig.json", "TypeScript"),
        ("pyproject.toml", "Python"),
        ("go.mod", "Go"),
        ("Cargo.toml", "Rust"),
        ("pubspec.yaml", "Flutter/Dart"),
        ("Package.swift", "Swift Package"),
    ]:
        if path in config_paths:
            signals.append(label)
    deps: list[str] = []
    for item in files:
        for dep in item.get("dependencies", []):
            if dep not in deps:
                deps.append(dep)
    notable = [
        dep
        for dep in deps
        if re.search(
            r"(react|vue|svelte|ink|commander|yargs|vitest|jest|tsup|vite|next|express"
            r"|fastify|openai|anthropic|langchain|mcp)",
            dep,
            re.I,
        )
    ]
    if notable:
        signals.append("关键依赖：" + "、".join(notable[:25]))
    return signals


def find_contract_files(files: list[dict]) -> list[dict]:
    return [
        item
        for item in files
        if re.search(
            r"(type|types|schema|contract|protocol|manifest|config|workflow|tool"
            r"|mcp|permission|guard|security|command)",
            item["path"],
            re.I,
        )
        or any(
            re.search(
                r"(Schema|Config|Options|Command|Tool|Workflow|Permission"
                r"|Protocol|Manifest|Message|Event)",
                symbol,
            )
            for symbol in item.get("symbols", [])
        )
    ]


def find_runtime_files(files: list[dict]) -> list[dict]:
    return [
        item
        for item in files
        if item["role"] in {"source", "config"}
        and re.search(
            r"(main|index|app|server|cli|repl|router|loop|executor"
            r"|orchestrator|controller|client|registry|manager)",
            item["path"],
            re.I,
        )
    ]


def find_by_path(files: list[dict], pattern: str) -> list[dict]:
    return [item for item in files if re.search(pattern, item["path"], re.I)]


def is_skill_project(files: list[dict]) -> bool:
    paths = {item["path"] for item in files}
    return "SKILL.md" in paths or (
        any(path.startswith("references/") for path in paths)
        and any(path.startswith("scripts/") for path in paths)
        and any(path.startswith("agents/") for path in paths)
    )


def is_agent_project(files: list[dict]) -> bool:
    paths = {item["path"] for item in files}
    path_text = "\n".join(paths)
    return bool(
        re.search(
            r"(^|/)(agents?|orchestrator|controller|tools?|mcp|llm|memory"
            r"|workflows?|prompts?)(/|$)",
            path_text,
            re.I,
        )
        or any(
            re.search(
                r"(agent|assistant|system-prompt|tool|mcp|llm|workflow|orchestrator|controller)",
                item["path"],
                re.I,
            )
            for item in files
        )
    )


def source_modules_with_tests(modules: dict[str, list[dict]]) -> list[str]:
    missing: list[str] = []
    for module, items in modules.items():
        has_source = any(item["role"] == "source" for item in items)
        has_test = any(item["role"] == "test" for item in items)
        if has_source and not has_test:
            missing.append(module)
    return missing


def append_file_list(
    lines: list[str], title: str, items: list[dict], limit: int = 30
) -> None:
    lines.extend([f"## {title}", ""])
    if items:
        for item in items[:limit]:
            detail = []
            if item.get("heading"):
                detail.append(item["heading"])
            if item.get("symbols"):
                detail.append("符号：" + ", ".join(item["symbols"][:8]))
            suffix = f"（{'；'.join(detail)}）" if detail else ""
            lines.append(f"- `{item['path']}`{suffix}")
    else:
        lines.append("- 未识别到明显文件。")
    lines.append("")


def safe_mermaid(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def escape(value: str) -> str:
    return value.replace('"', "'")


# --- 渲染函数 ---


def render_project_overview(scan_result: dict) -> str:
    files = scan_result["files"]
    modules = scan_result["modules"]
    docs = [f for f in files if f["role"] == "document"][:20]
    configs = [f for f in files if f["role"] == "config"][:30]
    source = [f for f in files if f["role"] == "source"]
    tests = [f for f in files if f["role"] == "test"]
    commands = []
    for item in configs:
        commands.extend(
            f"{item['path']} -> {command}"
            for command in item.get("commands", [])
        )
    entry_points = [
        f
        for f in source
        if Path(f["path"]).name.lower()
        in {
            "main.py", "main.ts", "main.js", "index.ts", "index.js",
            "app.ts", "app.js", "server.ts", "server.js",
        }
    ][:12]
    counts = role_counts(files)

    lines = [
        "# 项目摘要",
        "",
        f"项目根目录：`{scan_result['root']}`",
        f"项目 ID：`{scan_result['project_id']}`",
        f"扫描时间：{scan_result['scanned_at']}",
        "",
        "## 清单",
        "",
        f"- 已索引文件：{len(files)}",
        f"- 已索引模块：{len(modules)}",
    ]
    for role, count in counts.items():
        lines.append(f"- {ROLE_LABELS.get(role, role)}：{count}")

    lines.extend(["", "## 项目用途", ""])
    purpose_docs = [item for item in docs if item.get("excerpt")]
    if purpose_docs:
        for item in purpose_docs[:5]:
            lines.append(f"- `{item['path']}`：{item['excerpt']}")
    else:
        lines.append("- 未能从文档中提取项目用途；需要后续定向阅读。")

    lines.extend(["", "## 技术信号", ""])
    signals = technology_signals(files)
    if signals:
        for signal in signals:
            lines.append(f"- {signal}")
    elif not configs:
        lines.append("- 未发现常见配置文件。")
    if configs:
        lines.append("- 配置文件：")
        for item in configs:
            lines.append(f"  - `{item['path']}`")

    lines.extend(["", "## 文档信号", ""])
    if docs:
        for item in docs:
            heading = f" - {item['heading']}" if item["heading"] else ""
            lines.append(f"- `{item['path']}`{heading}")
    else:
        lines.append("- 未发现文档文件。")

    lines.extend(["", "## 源码与测试", ""])
    lines.append(f"- 源码文件：{len(source)}")
    lines.append(f"- 测试文件：{len(tests)}")
    source_with_comments = [item for item in source if item.get("code_comment")]
    if source_with_comments:
        lines.extend(["", "## 源码摘要", ""])
        for item in source_with_comments[:5]:
            lines.append(f"- `{item['path']}`：{item['code_comment']}")

    lines.extend(["", "## 入口与命令", ""])
    if entry_points:
        lines.append("- 可能入口文件：")
        for item in entry_points:
            lines.append(f"  - `{item['path']}`")
    else:
        lines.append("- 未识别出常见入口文件。")
    if commands:
        lines.append("- 配置命令：")
        for command in commands[:20]:
            lines.append(f"  - `{command}`")
    else:
        lines.append("- 未识别出配置命令。")

    lines.extend(["", "## 测试与质量门禁", ""])
    test_commands = [
        command
        for command in commands
        if re.search(r"\b(test|lint|check|typecheck|format)\b", command, re.I)
    ]
    if test_commands:
        for command in test_commands:
            lines.append(f"- `{command}`")
    elif tests:
        lines.append("- 存在测试文件，但未识别出测试命令。")
    else:
        lines.append("- 未识别出测试文件或测试命令。")

    lines.extend(["", "## 主要模块", ""])
    for module, module_files in list(modules.items())[:20]:
        roles = "、".join(
            ROLE_LABELS.get(role, role)
            for role in sorted({item["role"] for item in module_files})
        )
        lines.append(f"- `{module}`：{len(module_files)} 个文件；角色：{roles}")

    lines.extend(["", "## 后续建议阅读", ""])
    important = docs[:8] + configs[:8] + source[:12]
    for item in important:
        lines.append(f"- `{item['path']}`")
    if not important:
        lines.append("- 未识别出后续建议阅读文件。")

    lines.extend(["", "## 风险与未知点", ""])
    lines.append("- 当前是轻量扫描；修改前仍需对照源码验证行为。")
    lines.append("- import 关系可能包含未解析的外部包。")
    lines.append("- 产品定位、真实运行链路和安全边界只能从源码/文档推断。")
    return "\n".join(lines) + "\n"


def render_runtime_flow_brief(scan_result: dict) -> str:
    files = scan_result["files"]
    runtime_files = find_runtime_files(files)
    lines = ["# 运行链路", ""]
    if runtime_files:
        for item in runtime_files[:30]:
            symbols = (
                f"；符号：{', '.join(item['symbols'][:5])}"
                if item.get("symbols")
                else ""
            )
            lines.append(
                f"- `{item['path']}`（{ROLE_LABELS.get(item['role'], item['role'])}{symbols}）"
            )
    else:
        lines.append("- 未从文件名识别出入口、CLI、调度器、执行器或客户端文件。")
    return "\n".join(lines) + "\n"


def render_contracts_brief(scan_result: dict) -> str:
    files = scan_result["files"]
    contract_files = find_contract_files(files)
    lines = ["# 核心 Contract", ""]
    if contract_files:
        for item in contract_files[:30]:
            symbols = (
                f"；符号：{', '.join(item['symbols'][:8])}"
                if item.get("symbols")
                else ""
            )
            lines.append(
                f"- `{item['path']}`（{ROLE_LABELS.get(item['role'], item['role'])}{symbols}）"
            )
    else:
        lines.append("- 未识别出明显 contract 文件。")
    return "\n".join(lines) + "\n"


def render_risk_map_brief(scan_result: dict) -> str:
    files = scan_result["files"]
    modules = scan_result["modules"]
    large_files = sorted(
        [item for item in files if item["role"] in {"source", "test"}],
        key=lambda item: item["size_bytes"],
        reverse=True,
    )[:10]
    untested_modules = source_modules_with_tests(modules)
    lines = ["# 风险地图", ""]
    if large_files:
        lines.append("## 大文件")
        for item in large_files:
            lines.append(f"- `{item['path']}`：{item['size_bytes']} bytes")
        lines.append("")
    if untested_modules:
        lines.append("## 有源码但未发现测试")
        for module in untested_modules[:20]:
            lines.append(f"- `{module}`")
    return "\n".join(lines) + "\n"


def render_worktree(scan_result: dict) -> str:
    worktree = scan_result.get("worktree", {})
    lines = ["# 当前 Worktree 快照", ""]
    if not worktree.get("is_git_repo"):
        lines.append("- 当前项目根目录未识别为 git 仓库。")
        return "\n".join(lines) + "\n"
    lines.append(f"- 分支：`{worktree.get('branch') or '(detached/unknown)'}`")
    status = worktree.get("status", [])
    if status:
        lines.extend(["", "## 未提交改动", ""])
        for line in status:
            lines.append(f"- `{line}`")
        lines.extend(["", "## 使用提醒", ""])
        lines.append("- 这些改动可能来自用户或其他工具；后续任务不得擅自回滚。")
        lines.append(
            "- 修改前应判断相关文件是否已有未完成工作，并只改动本次任务需要的范围。"
        )
    else:
        lines.extend(["", "## 未提交改动", "", "- 无。"])
    return "\n".join(lines) + "\n"


def render_skill_summary_brief(scan_result: dict) -> str:
    files = scan_result["files"]
    lines = ["# Skill 项目专项摘要", ""]
    if not is_skill_project(files):
        lines.append("- 未识别到明确的 skill 项目信号。")
        return "\n".join(lines) + "\n"
    skill_files = find_by_path(files, r"(^|/)SKILL\.md$")
    references = find_by_path(files, r"(^|/)references?/")
    scripts = find_by_path(files, r"(^|/)scripts?/")
    if skill_files:
        lines.append("## 入口文件")
        for item in skill_files[:5]:
            lines.append(f"- `{item['path']}`")
    if references:
        lines.append("")
        lines.append("## References")
        for item in references[:10]:
            lines.append(f"- `{item['path']}`")
    if scripts:
        lines.append("")
        lines.append("## Scripts")
        for item in scripts[:10]:
            lines.append(f"- `{item['path']}`")
    return "\n".join(lines) + "\n"


def render_agent_summary_brief(scan_result: dict) -> str:
    files = scan_result["files"]
    lines = ["# Agent 项目专项摘要", ""]
    if not is_agent_project(files):
        lines.append("- 未识别到明确的 agent 项目信号。")
        return "\n".join(lines) + "\n"
    groups = [
        ("Agent/编排", r"(^|/)(agents?|orchestrator|controller|router|loop)(/|\.|-|$)"),
        ("工具与权限", r"(^|/)(tools?|permission|security|guard|approval|sandbox)(/|\.|-|$)"),
        ("MCP/插件", r"(^|/)(mcp|plugins?|skills?|hooks?)(/|\.|-|$)"),
    ]
    for title, pattern in groups:
        matched = find_by_path(files, pattern)[:10]
        if matched:
            lines.append(f"## {title}")
            for item in matched:
                lines.append(f"- `{item['path']}`")
            lines.append("")
    return "\n".join(lines) + "\n"


def render_mermaid(scan_result: dict) -> str:
    project = scan_result["project_id"]
    lines = [
        "# Mermaid 图谱",
        "",
        "```mermaid",
        "graph TD",
        f'  {safe_mermaid(project)}["{escape(scan_result["root"].split("/")[-1])}"]',
    ]
    for module, files in list(scan_result["modules"].items())[:30]:
        mod_id = stable_id("mod", module, module)
        lines.append(
            f'  {safe_mermaid(project)} --> {safe_mermaid(mod_id)}["{escape(module)}"]'
        )
        for item in files[:5]:
            lines.append(
                f'  {safe_mermaid(mod_id)} --> {safe_mermaid(item["id"])}["{escape(item["name"])}"]'
            )
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_full_summary(scan_result: dict) -> str:
    """将所有内容合并到一个文件中，供大模型快速读取。"""
    sections = []
    sections.append(render_project_overview(scan_result))
    sections.append(render_runtime_flow_brief(scan_result))
    sections.append(render_contracts_brief(scan_result))
    sections.append(render_risk_map_brief(scan_result))
    sections.append(render_worktree(scan_result))

    files = scan_result["files"]
    if is_skill_project(files):
        sections.append(render_skill_summary_brief(scan_result))
    if is_agent_project(files):
        sections.append(render_agent_summary_brief(scan_result))

    sections.append(render_mermaid(scan_result))
    return "\n\n---\n\n".join(sections)
