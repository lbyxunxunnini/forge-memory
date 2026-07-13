"""Chunk 级元数据提取：从源码文件中提取函数、类、文档、注释和 TODO，附带行范围。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .utils import stable_id


# --- Chunk 提取 Pattern ---

# 函数定义
_FUNC_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("python", re.compile(r"^(async\s+)?def\s+([A-Za-z_]\w*)", re.M)),
    ("typescript", re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w$]*)", re.M)),
    ("typescript", re.compile(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][\w$]*)\s*=\s*(?:async\s+)?\(", re.M)),
    ("dart", re.compile(r"^(?:\w+\s+)*([A-Za-z_]\w*)\s*\(", re.M)),
    ("go", re.compile(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?([A-Za-z_]\w*)", re.M)),
    ("java", re.compile(r"^\s*(?:public|private|protected|static|\s)*\s+\w+\s+([A-Za-z_]\w*)\s*\(", re.M)),
    ("swift", re.compile(r"^\s*func\s+([A-Za-z_]\w*)", re.M)),
]

# 类定义
_CLASS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("python", re.compile(r"^class\s+([A-Za-z_]\w*)", re.M)),
    ("typescript", re.compile(r"^(?:export\s+)?class\s+([A-Za-z_][\w$]*)", re.M)),
    ("typescript", re.compile(r"^(?:export\s+)?(?:interface|type|enum)\s+([A-Za-z_][\w$]*)", re.M)),
    ("dart", re.compile(r"^(?:abstract\s+)?class\s+([A-Za-z_]\w*)", re.M)),
    ("go", re.compile(r"^type\s+([A-Za-z_]\w*)\s+struct", re.M)),
    ("java", re.compile(r"^\s*(?:public|private|protected|abstract|\s)*\s*class\s+([A-Za-z_]\w*)", re.M)),
]

# 文档注释（docstring / JSDoc / block comment）
_DOCSTRING_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("python_docstring", re.compile(r'^(\s*)("""|\x27\x27\x27)', re.M)),
    ("jsdoc", re.compile(r"^\s*/\*\*", re.M)),
]

# 单行注释中的 TODO/FIXME/HACK
_TODO_PATTERN = re.compile(r"(?:#|//|;)\s*(TODO|FIXME|HACK|XXX|NOTE)\b[:\s]*(.*)", re.I)

# 单行注释
_COMMENT_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\s*(#.*)$", re.M),           # Python, Ruby, Shell
    re.compile(r"^\s*(//.*)$", re.M),           # JS/TS, Go, Java, Swift, Dart
    re.compile(r"^\s*(;.*)$", re.M),            # Lisp, Clojure
]


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _find_block_end(lines: list[str], start: int, marker: str) -> int:
    """找到 docstring/block comment 的结束行。"""
    # Python docstring: """ 或 '''
    if marker in ('"""', "'''"):
        # 同一行关闭
        rest = lines[start][lines[start].index(marker) + len(marker):]
        if marker in rest:
            return start
        for i in range(start + 1, min(start + 200, len(lines))):
            if marker in lines[i]:
                return i
        return min(start + 200, len(lines) - 1)

    # JSDoc: /* ... */
    if marker == "/**":
        for i in range(start + 1, min(start + 200, len(lines))):
            if "*/" in lines[i]:
                return i
        return min(start + 200, len(lines) - 1)

    return start


def _extract_function_body_range(lines: list[str], start: int) -> int:
    """估算函数体的结束行（基于缩进回退）。"""
    if start >= len(lines) - 1:
        return start
    # 获取函数定义的缩进级别
    def_line = lines[start]
    base_indent = len(def_line) - len(def_line.lstrip())
    # 查找缩进回退到同级或更低的行
    for i in range(start + 1, min(start + 500, len(lines))):
        line = lines[i]
        if not line.strip():  # 空行跳过
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= base_indent and line.strip():
            # 检查是否是同级的新定义（class/def/function）
            stripped = line.strip()
            if re.match(r"^(async\s+)?def\s|^class\s|^function\s|^export\s|^type\s|^interface\s", stripped):
                return i - 1
            # 如果缩进严格小于等于 base 且不是续行，可能是函数结束
            if current_indent < base_indent:
                return i - 1
    return min(start + 500, len(lines) - 1)


def extract_chunks(file_path: str, text: str) -> list[dict]:
    """从源码文本中提取 chunk 元数据。

    返回 list[dict]，每个 dict 包含:
    - id: chunk 稳定 ID
    - file_path: 文件相对路径
    - line_start: 起始行号 (1-based)
    - line_end: 结束行号 (1-based, inclusive)
    - type: function / class / docstring / comment / todo
    - name: 名称（函数名、类名、TODO 标签等）
    - summary: 前 200 字符的摘要
    - content_hash: 内容 hash
    """
    lines = text.splitlines()
    if not lines:
        return []

    chunks: list[dict] = []
    seen_ranges: set[tuple[int, int]] = set()

    # 1. 提取函数
    for lang, pattern in _FUNC_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(match.lastindex) if match.lastindex else match.group(1)
            line_num = text[:match.start()].count("\n") + 1
            body_end = _extract_function_body_range(lines, line_num - 1)
            key = (line_num, body_end + 1)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            chunk_text = "\n".join(lines[line_num - 1:body_end + 1])
            chunks.append({
                "id": stable_id("chunk", f"{file_path}:func:{name}:{line_num}", name),
                "file_path": file_path,
                "line_start": line_num,
                "line_end": body_end + 1,
                "type": "function",
                "name": name,
                "summary": chunk_text[:200].replace("\n", " ").strip(),
                "content_hash": _content_hash(chunk_text),
            })

    # 2. 提取类
    for lang, pattern in _CLASS_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(match.lastindex) if match.lastindex else match.group(1)
            line_num = text[:match.start()].count("\n") + 1
            body_end = _extract_function_body_range(lines, line_num - 1)
            key = (line_num, body_end + 1)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            chunk_text = "\n".join(lines[line_num - 1:body_end + 1])
            chunks.append({
                "id": stable_id("chunk", f"{file_path}:class:{name}:{line_num}", name),
                "file_path": file_path,
                "line_start": line_num,
                "line_end": body_end + 1,
                "type": "class",
                "name": name,
                "summary": chunk_text[:200].replace("\n", " ").strip(),
                "content_hash": _content_hash(chunk_text),
            })

    # 3. 提取 docstring / JSDoc
    for doc_type, pattern in _DOCSTRING_PATTERNS:
        for match in pattern.finditer(text):
            line_num = text[:match.start()].count("\n") + 1
            marker = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(0).strip()
            end_line = _find_block_end(lines, line_num - 1, marker if marker else "/**")
            key = (line_num, end_line + 1)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            chunk_text = "\n".join(lines[line_num - 1:end_line + 1])
            # 尝试提取 docstring 的第一行作为名称
            first_content = chunk_text.strip().split("\n", 1)
            name_hint = first_content[1].strip()[:80] if len(first_content) > 1 else "doc"
            chunks.append({
                "id": stable_id("chunk", f"{file_path}:doc:{line_num}", name_hint),
                "file_path": file_path,
                "line_start": line_num,
                "line_end": end_line + 1,
                "type": "docstring",
                "name": name_hint,
                "summary": chunk_text[:200].replace("\n", " ").strip(),
                "content_hash": _content_hash(chunk_text),
            })

    # 4. 提取 TODO/FIXME/HACK
    for match in _TODO_PATTERN.finditer(text):
        line_num = text[:match.start()].count("\n") + 1
        tag = match.group(1).upper()
        desc = match.group(2).strip()[:120]
        key = (line_num, line_num)
        if key in seen_ranges:
            continue
        seen_ranges.add(key)
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        chunks.append({
            "id": stable_id("chunk", f"{file_path}:todo:{tag}:{line_num}", desc),
            "file_path": file_path,
            "line_start": line_num,
            "line_end": line_num,
            "type": "todo",
            "name": f"{tag}: {desc}",
            "summary": line_text.strip()[:200],
            "content_hash": _content_hash(line_text),
        })

    # 按行号排序
    chunks.sort(key=lambda c: (c["line_start"], c["line_end"]))
    return chunks
