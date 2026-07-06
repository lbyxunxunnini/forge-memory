"""任务级上下文包生成器。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .utils import ROLE_LABELS, branch_context_path, current_branch, stable_id


# 中文→英文 常见开发术语映射（用于跨语言关键词匹配）
_ZH_EN_MAP: dict[str, list[str]] = {
    "播放": ["player", "play", "audio", "media"],
    "播放器": ["player", "controller"],
    "歌曲": ["song", "track", "music"],
    "音乐": ["music", "audio", "song"],
    "订阅": ["subscription", "subscribe", "plan"],
    "登录": ["login", "auth", "signin"],
    "注册": ["register", "signup"],
    "用户": ["user", "account", "profile"],
    "设置": ["setting", "config", "preference"],
    "搜索": ["search", "query", "find"],
    "列表": ["list", "index", "feed"],
    "详情": ["detail", "info", "page"],
    "编辑": ["edit", "update", "modify"],
    "删除": ["delete", "remove", "destroy"],
    "创建": ["create", "new", "add"],
    "上传": ["upload", "import"],
    "下载": ["download", "export"],
    "支付": ["payment", "pay", "checkout"],
    "订单": ["order", "purchase"],
    "消息": ["message", "notification", "msg"],
    "通知": ["notification", "alert", "push"],
    "首页": ["home", "main", "index"],
    "个人": ["profile", "me", "account"],
    "我的": ["my", "profile", "me"],
    "评论": ["comment", "review", "feedback"],
    "分享": ["share", "social"],
    "收藏": ["favorite", "bookmark", "collect"],
    "历史": ["history", "record", "log"],
    "推荐": ["recommend", "suggestion", "feed"],
    "卡顿": ["lag", "jank", "slow", "performance", "frame"],
    "闪退": ["crash", "exception", "error"],
    "修复": ["fix", "bug", "patch", "repair"],
    "优化": ["optimize", "improve", "performance"],
    "重构": ["refactor", "restructure"],
    "测试": ["test", "spec", "verify"],
    "界面": ["ui", "view", "screen", "page"],
    "路由": ["route", "navigation", "navigator"],
    "状态": ["state", "status", "provider", "bloc"],
    "网络": ["network", "http", "api", "request"],
    "缓存": ["cache", "storage", "local"],
    "数据库": ["database", "db", "sqlite", "hive"],
    "权限": ["permission", "access", "auth"],
    "配置": ["config", "setting", "env"],
    "主题": ["theme", "style", "color"],
    "动画": ["animation", "animate", "transition"],
    "图片": ["image", "photo", "picture", "img"],
    "视频": ["video", "player"],
    "录音": ["record", "audio", "recording"],
    "歌词": ["lyric", "lyrics", "text"],
    "封面": ["cover", "artwork", "thumbnail"],
    "歌单": ["playlist", "album", "collection"],
    "歌手": ["artist", "singer"],
    "专辑": ["album", "release"],
    "标签": ["tag", "label", "category"],
    "分类": ["category", "type", "group"],
    "模块": ["module", "component"],
    "组件": ["widget", "component", "view"],
    "控制器": ["controller", "handler", "manager"],
    "服务": ["service", "api", "repository"],
    "工具": ["tool", "util", "helper"],
    "管理": ["manager", "admin", "manage"],
    "页面": ["page", "screen", "view"],
    "弹窗": ["dialog", "popup", "modal", "bottomsheet"],
    "底部栏": ["bottombar", "navbar", "tabbar"],
    "顶部栏": ["appbar", "toolbar", "header"],
    "侧边栏": ["sidebar", "drawer", "menu"],
    "表单": ["form", "input", "field"],
    "按钮": ["button", "btn", "action"],
    "卡片": ["card", "item", "tile"],
    "轮播": ["carousel", "slider", "swiper"],
    "刷新": ["refresh", "reload", "pull"],
    "加载": ["loading", "loader", "progress"],
    "错误": ["error", "exception", "failure"],
    "成功": ["success", "complete", "done"],
}


def _extract_keywords(task: str) -> list[str]:
    """从任务描述中提取关键词，支持中英文混合。"""
    stopwords = {
        "的", "了", "在", "是", "和", "与", "或", "不", "有", "这", "那",
        "我", "你", "他", "她", "它", "们", "个", "把", "被", "从", "到",
        "对", "为", "以", "用", "将", "会", "能", "可", "要", "做",
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into",
        "about", "between", "through", "during", "before", "after",
        "and", "but", "or", "not", "no", "nor", "so", "yet",
        "it", "its", "this", "that", "these", "those",
        "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
        "my", "your", "his", "our", "their",
    }

    # 1. 提取英文单词
    en_tokens = re.findall(r"[a-zA-Z_][\w]*", task.lower())
    en_keywords = [t for t in en_tokens if t not in stopwords and len(t) > 1]

    # 2. 提取中文词组（连续中文字符序列）
    zh_segments = re.findall(r"[一-鿿]+", task)

    # 3. 中文→英文翻译：贪心最长匹配，提取所有匹配子短语
    translated: list[str] = []
    for seg in zh_segments:
        pos = 0
        matched_any = False
        while pos < len(seg):
            # 从当前位置开始，尝试最长匹配
            best_len = 0
            best_translations: list[str] = []
            for length in range(min(len(seg) - pos, 6), 1, -1):
                chunk = seg[pos : pos + length]
                if chunk in _ZH_EN_MAP:
                    best_len = length
                    best_translations = _ZH_EN_MAP[chunk]
                    break
            if best_len > 0:
                translated.extend(best_translations)
                pos += best_len
                matched_any = True
            else:
                pos += 1
        # 如果没有匹配到映射，用 2-char n-gram 作为中文关键词
        if not matched_any and len(seg) >= 2:
            for i in range(len(seg) - 1):
                ngram = seg[i : i + 2]
                if ngram not in stopwords:
                    translated.append(ngram)

    # 4. 合并去重，英文关键词优先
    seen: set[str] = set()
    keywords: list[str] = []
    for kw in en_keywords + translated:
        if kw not in seen:
            seen.add(kw)
            keywords.append(kw)

    return keywords


def _read_index(context: Path) -> tuple[list[dict], list[dict]]:
    """读取 index/files.jsonl 和 index/modules.jsonl。"""
    files: list[dict] = []
    modules: list[dict] = []

    files_path = context / "index" / "files.jsonl"
    if files_path.exists():
        for line in files_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    files.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    modules_path = context / "index" / "modules.jsonl"
    if modules_path.exists():
        for line in modules_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    modules.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return files, modules


def _score_file(
    file_record: dict,
    keywords: list[str],
    en_keywords: list[str],
    entry_files: list[str] | None,
) -> float:
    """为文件打相关性分。英文原始关键词权重高于翻译关键词。"""
    score = 0.0
    path_lower = file_record["path"].lower()
    name_lower = file_record.get("name", "").lower()
    symbols = [s.lower() for s in file_record.get("symbols", [])]
    module = file_record.get("module", "").lower()

    # 入口文件加分
    if entry_files and file_record["path"] in entry_files:
        score += 100.0

    for kw in keywords:
        # 英文原始关键词权重更高
        weight = 1.5 if kw in en_keywords else 1.0

        if kw in path_lower:
            score += 10.0 * weight
        if kw in name_lower:
            score += 8.0 * weight
        if any(kw in s for s in symbols):
            score += 6.0 * weight
        if kw in module:
            score += 4.0 * weight
        if kw in file_record.get("heading", "").lower():
            score += 3.0 * weight
        if kw in file_record.get("excerpt", "").lower():
            score += 2.0 * weight

    return score


def generate_context_pack(
    root: Path,
    task: str,
    entry_files: list[str] | None = None,
) -> str:
    """生成上下文包 Markdown。"""
    branch = current_branch(root)
    context = branch_context_path(root, branch)
    keywords = _extract_keywords(task)
    # 提取英文原始关键词（用于加权评分）
    en_keywords = set(re.findall(r"[a-zA-Z_][\w]*", task.lower()))
    files, modules = _read_index(context)

    if not files:
        return "# Forge Memory Context Pack\n\n## Task\n\n" + task + "\n\n## Caveats\n\n- 未找到索引数据。请先运行 forge-memory scan。\n"

    # 打分并排序
    scored = []
    for f in files:
        score = _score_file(f, keywords, en_keywords, entry_files)
        if score > 0:
            scored.append((score, f))
    scored.sort(key=lambda x: x[0], reverse=True)

    related_files = [f for _, f in scored[:30]]
    related_modules = []
    seen_modules: set[str] = set()
    for f in related_files:
        mod = f.get("module", "")
        if mod and mod not in seen_modules:
            seen_modules.add(mod)
            related_modules.append(mod)

    # 风险点
    large_files = [f for f in files if f.get("size_bytes", 0) > 50000 and f["role"] in {"source", "test"}]
    import_heavy = [f for f in files if len(f.get("imports", [])) > 10]

    # 无测试模块
    module_roles: dict[str, set[str]] = {}
    for f in files:
        mod = f.get("module", "")
        if mod:
            module_roles.setdefault(mod, set()).add(f["role"])
    untested = [mod for mod, roles in module_roles.items() if "source" in roles and "test" not in roles]

    # 建议测试
    suggested_tests = []
    for mod in related_modules:
        if mod in untested:
            mod_files = [f for f in files if f.get("module") == mod and f["role"] == "source"]
            for f in mod_files[:3]:
                suggested_tests.append(f["path"])

    # 置信度
    match_ratio = len(related_files) / max(len(files), 1)
    if match_ratio > 0.05 and len(related_files) >= 5:
        confidence = "high"
    elif match_ratio > 0.01 and len(related_files) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # 生成 Markdown
    lines = [
        "# Forge Memory Context Pack",
        "",
        "## Task",
        "",
        task,
        "",
        "## Likely Entry Files",
        "",
    ]
    if related_files:
        for f in related_files[:15]:
            role = ROLE_LABELS.get(f["role"], f["role"])
            lines.append(f"- `{f['path']}` ({role})")
    else:
        lines.append("- 未找到明显相关文件。")

    lines.extend(["", "## Related Modules", ""])
    if related_modules:
        for mod in related_modules[:10]:
            lines.append(f"- `{mod}`")
    else:
        lines.append("- 未找到明显相关模块。")

    lines.extend(["", "## Recent Changes", ""])
    # 读取 commits.jsonl 获取近期涉及相关文件的 commit
    commits_path = context / "index" / "commits.jsonl"
    commit_files_path = context / "index" / "commit_files.jsonl"
    if commits_path.exists() and commit_files_path.exists():
        related_paths = {f["path"] for f in related_files}
        commits_data = {}
        for line in commits_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    c = json.loads(line)
                    commits_data[c["hash"]] = c
                except json.JSONDecodeError:
                    continue
        relevant_hashes: set[str] = set()
        for line in commit_files_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    cf = json.loads(line)
                    if cf["file_path"] in related_paths:
                        relevant_hashes.add(cf["commit_hash"])
                except json.JSONDecodeError:
                    continue
        relevant_commits = sorted(
            [commits_data[h] for h in relevant_hashes if h in commits_data],
            key=lambda c: c.get("date", ""), reverse=True,
        )[:10]
        if relevant_commits:
            for c in relevant_commits:
                lines.append(f"- `{c['short_hash']}` {c['date'][:10]} {c['message']}")
        else:
            lines.append("- 未找到与相关文件匹配的近期 commit。")
    else:
        lines.append("- 未找到 Git 历史数据。请运行 forge-memory scan。")

    lines.extend(["", "## Dependency / Impact", ""])
    if import_heavy:
        lines.append("### 高导入文件")
        for f in import_heavy[:10]:
            lines.append(f"- `{f['path']}`：{len(f.get('imports', []))} 个 import")
    else:
        lines.append("- 未识别到高导入文件。")

    lines.extend(["", "## Risk Points", ""])
    if large_files:
        lines.append("### 大文件")
        for f in large_files[:10]:
            lines.append(f"- `{f['path']}`：{f.get('size_bytes', 0)} bytes")
    if untested:
        lines.append("")
        lines.append("### 有源码但无测试的模块")
        for mod in untested[:15]:
            lines.append(f"- `{mod}`")
    if not large_files and not untested:
        lines.append("- 未识别到明显风险点。")

    lines.extend(["", "## Suggested Tests", ""])
    if suggested_tests:
        for t in suggested_tests[:10]:
            lines.append(f"- `{t}`")
    else:
        lines.append("- 未找到建议的测试文件。")

    lines.extend(["", "## Evidence And Caveats", ""])
    lines.append(f"- 置信度：**{confidence}**")
    lines.append(f"- 匹配关键词：{', '.join(keywords[:10]) if keywords else '(无)'}")
    lines.append(f"- 相关文件数：{len(related_files)}")
    lines.append(f"- 总文件数：{len(files)}")
    if confidence == "low":
        lines.append("")
        lines.append("> **Caveat**: 置信度较低。任务描述与项目索引的匹配度不足，")
        lines.append("> 上下文包可能遗漏关键文件或包含不相关内容。建议结合源码阅读验证。")
    lines.append("")
    lines.append("- 本上下文包基于轻量索引匹配生成，不替代源码级验证。")
    lines.append("- import 关系可能包含未解析的外部包。")

    return "\n".join(lines) + "\n"
