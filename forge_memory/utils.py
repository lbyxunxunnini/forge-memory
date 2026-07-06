"""Forge Memory 工具函数：ID 生成、排除规则、路径工具、content_hash 计算。"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


# --- 排除规则 ---

EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    ".project-context",
    ".venv", "venv",
    "node_modules", "vendor",
    "dist", "build", "out", "target", ".next", ".cache",
    "__pycache__",
    ".dart_tool", ".gradle", ".cxx",
    ".trae", ".cursor", ".vscode", ".idea",
}

EXCLUDE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".pdf", ".zip", ".gz", ".tar", ".7z", ".dmg",
    ".mp4", ".mov", ".mp3",
    ".ttf", ".woff", ".woff2",
    ".lockb", ".map", ".log",
}

CONFIG_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt",
    "pom.xml", "build.gradle", "settings.gradle",
    "Cargo.toml", "go.mod", "pubspec.yaml",
    "Package.swift", "composer.json", "Gemfile",
    "Dockerfile", "docker-compose.yml",
    "tsconfig.json", "vite.config.ts", "next.config.js",
    "tailwind.config.js", "tsup.config.ts", "vitest.config.ts",
    "eslint.config.js", "eslint.config.mjs",
    "jest.config.js", "webpack.config.js", "rollup.config.js",
}

DOC_PATTERNS = re.compile(
    r"(readme|agent|claude|skill|architecture|design|roadmap|plan"
    r"|changelog|contributing|quickstart|adr|decision|protocol|contract|api)",
    re.I,
)

LANG_BY_SUFFIX = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".dart": "dart", ".swift": "swift", ".go": "go", ".rs": "rust",
    ".java": "java", ".kt": "kotlin", ".rb": "ruby", ".php": "php",
    ".cs": "csharp",
    ".md": "markdown", ".json": "json",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
}

ROLE_LABELS = {
    "config": "配置", "document": "文档",
    "source": "源码", "test": "测试", "other": "其他",
}

GENERATED_MARKER = "<!-- generated-by: forge-memory; safe-to-overwrite -->"

PLACEHOLDER_SNIPPETS = {
    "尚未扫描。",
    "尚未记录决策。",
    "尚未记录会话。",
    "Not scanned yet.",
    "No decisions recorded yet.",
    "No sessions recorded yet.",
}

SYMBOL_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w$]*)", re.M),
    re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_][\w$]*)", re.M),
    re.compile(r"^\s*export\s+(?:interface|type|enum)\s+([A-Za-z_][\w$]*)", re.M),
    re.compile(r"^\s*export\s+const\s+([A-Za-z_][\w$]*)", re.M),
    re.compile(r"^\s*def\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"^\s*(?:public\s+)?(?:struct|enum|class|func)\s+([A-Za-z_]\w*)", re.M),
]

IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]", re.M),
    re.compile(r"^\s*import\s+([A-Za-z0-9_./-]+)", re.M),
    re.compile(r"^\s*from\s+([A-Za-z0-9_./-]+)\s+import\s+", re.M),
    re.compile(r"^\s*require\(['\"]([^'\"]+)['\"]\)", re.M),
]

PROJECT_SIGNAL_NAMES = {
    "README.md", "AGENTS.md", "CLAUDE.md", "SKILL.md",
    "package.json", "pyproject.toml", "requirements.txt",
    "go.mod", "Cargo.toml", "pubspec.yaml",
}

PROJECT_SIGNAL_DIRS = {"src", "lib", "app", "packages", "apps", "services", "tests"}


# --- 工具函数 ---

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slugify(value: str, fallback: str = "item") -> str:
    out = []
    last_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            last_dash = False
        elif not last_dash:
            out.append("-")
            last_dash = True
    slug = "".join(out).strip("-")
    return slug or fallback


def stable_id(kind: str, key: str, name: str | None = None) -> str:
    slug = slugify(name or key)
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"{kind}-{slug[:48]}-{digest}"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip_file(path: Path) -> bool:
    return path.suffix.lower() in EXCLUDE_SUFFIXES


def is_text_file(path: Path, max_bytes: int) -> bool:
    try:
        data = path.read_bytes()[: min(max_bytes, 4096)]
    except OSError:
        return False
    return b"\x00" not in data


def read_text(path: Path, max_bytes: int) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def has_project_signal(root: Path) -> bool:
    for name in PROJECT_SIGNAL_NAMES:
        if (root / name).exists():
            return True
    for name in PROJECT_SIGNAL_DIRS:
        if (root / name).is_dir():
            return True
    return any(child.is_file() for child in root.iterdir())


def generated_md(content: str) -> str:
    return f"{GENERATED_MARKER}\n{content}"


def safe_to_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8", errors="replace")
    if GENERATED_MARKER in text:
        return True
    return any(snippet in text for snippet in PLACEHOLDER_SNIPPETS)
