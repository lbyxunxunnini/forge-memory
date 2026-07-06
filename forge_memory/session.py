"""会话记忆管理：add_session 和 list_sessions。迁移自 project-memory。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .utils import now_iso, slugify, stable_id


def _stable_session_id(date_str: str, title: str, body: str) -> str:
    import hashlib

    key = f"{date_str}:{title}:{body[:500]}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"sess-{date_str.replace('-', '')}-{slugify(title)[:32]}-{digest}"


def _normalize_body(body: str) -> str:
    body = body.strip()
    if not body:
        return "## 摘要\n\n未提供摘要正文。\n"
    if re.search(r"^##\s+(Summary|摘要)", body, re.M):
        return body + "\n"
    return "## 摘要\n\n" + body + "\n"


def _validate_body(raw_body: str, normalized_body: str, allow_incomplete: bool) -> None:
    if not raw_body.strip():
        raise ValueError("会话摘要正文为空；请提供摘要正文，或先整理后再写入。")
    if allow_incomplete:
        return
    required_sections = ["摘要", "决策", "已变更或重要文件", "未决问题", "下一步"]
    missing = [
        section
        for section in required_sections
        if not re.search(
            rf"^##\s+{re.escape(section)}\s*$", normalized_body, re.M
        )
    ]
    if missing:
        raise ValueError(
            "会话摘要缺少必需章节：" + "、".join(missing) + "。"
            "如需临时写入不完整摘要，请添加 --allow-incomplete。"
        )


def _update_index(index_path: Path, title: str, date_str: str, session_id: str, filename: str) -> None:
    line = f"- {date_str} `{session_id}` [{title}]({filename})"
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else "# 会话摘要\n"
    lines = [
        item
        for item in existing.splitlines()
        if "No sessions recorded yet." not in item and "尚未记录会话。" not in item
    ]
    if line not in lines:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(line)
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def add_session(
    root: Path,
    title: str,
    body: str,
    allow_incomplete: bool = False,
) -> str:
    """添加会话摘要，返回 session_id。"""
    sessions = root / ".project-context" / "sessions"
    if not sessions.exists():
        raise FileNotFoundError("缺少 .project-context/sessions。请先运行 init。")

    raw_body = body
    body = _normalize_body(raw_body)
    _validate_body(raw_body, body, allow_incomplete)

    timestamp = now_iso()
    date_str = timestamp[:10]
    session_id = _stable_session_id(date_str, title, body)
    filename = f"{date_str}__{session_id}__{slugify(title)}.md"
    path = sessions / filename

    content = f"""---
id: {session_id}
title: {title}
date: {date_str}
created_at: {timestamp}
---

# {title}

日期：{date_str}
会话 ID：{session_id}

{body}
"""
    path.write_text(content, encoding="utf-8")
    _update_index(sessions / "index.md", title, date_str, session_id, filename)
    return session_id


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def list_sessions(root: Path) -> list[dict[str, str]]:
    """列出 .project-context/sessions 中的会话摘要。"""
    sessions_dir = root / ".project-context" / "sessions"
    if not sessions_dir.exists():
        raise FileNotFoundError("缺少 .project-context/sessions。请先运行 init。")

    records: list[dict[str, str]] = []
    for path in sorted(sessions_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = _parse_frontmatter(text)
        records.append(
            {
                "id": meta.get("id", ""),
                "title": meta.get("title", path.stem),
                "date": meta.get("date", ""),
                "created_at": meta.get("created_at", ""),
                "path": str(path),
            }
        )
    records.sort(key=lambda item: (item["date"], item["created_at"], item["path"]), reverse=True)
    return records
