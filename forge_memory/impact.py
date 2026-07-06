"""影响分析：导入关系、同模块文件、近期 commit、风险信号。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
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


def target_path_stem(file_path: str) -> str:
    """返回文件路径去掉扩展名的部分，如 lib/foo/bar.dart → lib/foo/bar"""
    return file_path.rsplit(".", 1)[0] if "." in file_path.rsplit("/", 1)[-1] else file_path


def _import_matches_file(import_path: str, file_path: str, file_stem: str) -> bool:
    """判断 import 路径是否指向指定文件。

    匹配规则：
    1. package:foo/lib/path → 去掉 package:foo/ 后与 file_stem 比较
    2. 相对路径 ../path → 用文件名末段匹配
    3. 以上都不匹配时返回 False（不再用子串匹配）
    """
    if not file_stem:
        return False

    # 去掉引号和分号
    imp = import_path.strip("'\"").rstrip(";").strip()

    # Dart package import: package:foo/bar.dart → lib/bar
    if imp.startswith("package:"):
        parts = imp.split("/", 1)
        if len(parts) == 2:
            pkg_stem = parts[1].rsplit(".", 1)[0] if "." in parts[1].rsplit("/", 1)[-1] else parts[1]
            # Dart: package:foo/path → lib/path
            return pkg_stem == file_stem or ("lib/" + pkg_stem) == file_stem

    # 相对路径：用文件名末段匹配
    imp_name = imp.rsplit("/", 1)[-1].rsplit(".", 1)[0] if "/" in imp else imp.rsplit(".", 1)[0]
    file_name = file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if imp_name and file_name and imp_name == file_name:
        return True

    # 绝对路径匹配（import 路径去掉扩展名 == file_stem）
    imp_stem = imp.rsplit(".", 1)[0] if "." in imp.rsplit("/", 1)[-1] else imp
    return imp_stem == file_stem


def _module_of(file_path: str) -> str:
    """从文件路径推断模块（目录部分）。"""
    parts = file_path.split("/")
    if len(parts) <= 1:
        return "."
    return "/".join(parts[:-1])


def _suggest_test(file_path: str) -> str:
    """将源码路径映射为测试路径。"""
    if file_path.startswith("lib/"):
        return "test/" + file_path[4:].replace(".dart", "_test.dart")
    if file_path.startswith("src/"):
        return "test/" + file_path[4:].replace(".py", "_test.py").replace(".ts", ".test.ts")
    return "test/" + file_path


def analyze_impact(root: Path, file_path: str, context: Path) -> dict:
    """分析文件影响。"""
    files = _load_jsonl(context / "index" / "files.jsonl")
    modules = _load_jsonl(context / "index" / "modules.jsonl")
    commits = _load_jsonl(context / "index" / "commits.jsonl")
    commit_files = _load_jsonl(context / "index" / "commit_files.jsonl")

    # 文件索引
    file_by_path = {f["path"]: f for f in files}
    target = file_by_path.get(file_path)
    if not target:
        return {"error": f"文件 {file_path} 不在索引中"}

    # 直接导入：找到 import 了目标文件的其他文件
    direct_importers = []
    target_stem = target_path_stem(file_path)
    for f in files:
        if f["path"] == file_path:
            continue
        for imp in f.get("imports", []):
            if _import_matches_file(imp, file_path, target_stem):
                direct_importers.append(f["path"])
                break

    # 直接依赖：目标文件 import 的其他文件
    direct_deps = []
    for imp in target.get("imports", []):
        for f in files:
            f_stem = target_path_stem(f["path"])
            if _import_matches_file(imp, f["path"], f_stem):
                direct_deps.append(f["path"])
                break

    # 同模块文件
    target_module = _module_of(file_path)
    module_files = [f["path"] for f in files if _module_of(f["path"]) == target_module and f["path"] != file_path]

    # 近期 commit（涉及该文件的最近 10 个）
    file_commits = []
    for cf in commit_files:
        if cf["file_path"] == file_path:
            # 找对应 commit
            for c in commits:
                if c["hash"] == cf["commit_hash"]:
                    file_commits.append(c)
                    break
    file_commits = file_commits[:10]

    # 风险信号
    risk_signals = []
    # 高频变更
    change_count = len([cf for cf in commit_files if cf["file_path"] == file_path])
    if change_count >= 5:
        risk_signals.append(f"高频变更：该文件在 {len(commits)} 个 commit 中被修改 {change_count} 次")

    # 缺少测试
    test_path = _suggest_test(file_path)
    test_exists = any(f["path"] == test_path for f in files)
    if not test_exists:
        risk_signals.append(f"缺少测试：未找到 {test_path}")

    # 建议测试
    suggested_tests = []
    if not test_exists:
        suggested_tests.append(test_path)

    return {
        "file": file_path,
        "direct_importers": direct_importers[:20],
        "direct_dependencies": direct_deps[:20],
        "module": target_module,
        "module_files": module_files[:20],
        "recent_commits": [
            {
                "hash": c["short_hash"],
                "date": c["date"][:10],
                "message": c["message"],
            }
            for c in file_commits
        ],
        "risk_signals": risk_signals,
        "suggested_tests": suggested_tests,
        "change_count": change_count,
    }


def format_impact(result: dict) -> str:
    """格式化影响分析输出。"""
    if "error" in result:
        return f"错误：{result['error']}"

    lines = [f"=== Impact Analysis: {result['file']} ===", ""]

    lines.append("直接导入该文件的:")
    if result["direct_importers"]:
        for p in result["direct_importers"]:
            lines.append(f"  - {p}")
    else:
        lines.append("  （无）")

    lines.append("")
    lines.append("该文件依赖的:")
    if result["direct_dependencies"]:
        for p in result["direct_dependencies"]:
            lines.append(f"  - {p}")
    else:
        lines.append("  （无）")

    lines.append("")
    lines.append(f"同模块文件 ({result['module']}):")
    if result["module_files"]:
        for p in result["module_files"][:10]:
            lines.append(f"  - {p}")
    else:
        lines.append("  （无）")

    lines.append("")
    lines.append("近期 Commit:")
    if result["recent_commits"]:
        for c in result["recent_commits"]:
            lines.append(f"  - {c['hash']} {c['date']} {c['message']}")
    else:
        lines.append("  （无）")

    lines.append("")
    lines.append("风险信号:")
    if result["risk_signals"]:
        for r in result["risk_signals"]:
            lines.append(f"  - {r}")
    else:
        lines.append("  （无）")

    if result["suggested_tests"]:
        lines.append("")
        lines.append("建议测试:")
        for t in result["suggested_tests"]:
            lines.append(f"  - {t}")

    return "\n".join(lines)
