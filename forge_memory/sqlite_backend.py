"""SQLite 后端：JSONL 导入、查询。"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS files (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  name TEXT,
  role TEXT,
  language TEXT,
  size_bytes INTEGER,
  content_hash TEXT,
  module_id TEXT,
  symbols TEXT,
  imports TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS modules (
  id TEXT PRIMARY KEY,
  name TEXT,
  root_path TEXT,
  file_count INTEGER,
  roles TEXT,
  summary TEXT
);

CREATE TABLE IF NOT EXISTS commits (
  hash TEXT PRIMARY KEY,
  short_hash TEXT,
  author TEXT,
  date TEXT,
  message TEXT,
  files_changed INTEGER,
  insertions INTEGER,
  deletions INTEGER
);

CREATE TABLE IF NOT EXISTS commit_files (
  commit_hash TEXT,
  file_path TEXT,
  change_type TEXT,
  PRIMARY KEY (commit_hash, file_path)
);

CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY,
  type TEXT,
  name TEXT,
  path TEXT,
  summary TEXT,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS edges (
  from_id TEXT,
  to_id TEXT,
  type TEXT,
  source TEXT,
  confidence TEXT,
  summary TEXT,
  PRIMARY KEY (from_id, to_id, type)
);

CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_module_id ON files(module_id);
CREATE INDEX IF NOT EXISTS idx_commit_files_path ON commit_files(file_path);
CREATE INDEX IF NOT EXISTS idx_commit_files_hash ON commit_files(commit_hash);
"""


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


def import_jsonl_to_sqlite(context: Path, branch: str, max_retries: int = 1) -> str:
    """将 JSONL 数据导入 SQLite，返回 .db 文件路径。

    Args:
        context: .project-context 或 branches/<branch> 路径
        branch: 分支名
        max_retries: 最大重试次数（从 .db.bak 恢复）

    Returns:
        (db_path, counts) 元组
    """
    from .utils import branch_context_path

    # 兼容：context 可能是 .project-context 或 branches/<branch>
    if (context / "index").exists():
        branch_dir = context
    else:
        root = context.parent.parent
        branch_dir = branch_context_path(root, branch)

    db_path = branch_dir / "forge-memory.db"
    # 备份旧文件
    if db_path.exists():
        import shutil
        backup_path = db_path.with_suffix(".db.bak")
        try:
            shutil.copy2(str(db_path), str(backup_path))
        except OSError as e:
            print(f"[IndexError] 无法备份数据库：{e} → 导入失败时将无法自动恢复", file=sys.stderr)

    for attempt in range(max_retries + 1):
        try:
            return _do_import(db_path, branch_dir)
        except Exception as e:
            import shutil
            if attempt < max_retries:
                # 从备份恢复
                backup_path = db_path.with_suffix(".db.bak")
                if backup_path.exists():
                    try:
                        shutil.copy2(str(backup_path), str(db_path))
                    except OSError as restore_err:
                        print(f"[IndexError] 备份恢复失败：{restore_err} → 后续重试可能仍失败，请检查文件权限", file=sys.stderr)
                print(f"[IndexError] 导入失败（第 {attempt + 1} 次）：{e} → 正在从备份恢复并重试...", file=sys.stderr)
            else:
                print(f"[IndexError] 导入失败（已重试 {max_retries} 次）：{e}", file=sys.stderr)
                backup_path = db_path.with_suffix(".db.bak")
                if backup_path.exists():
                    print(f"人工干预：从备份恢复 → cp {backup_path} {db_path}", file=sys.stderr)
                else:
                    print(f"人工干预：重新扫描 → python3 forge_memory.py scan {branch_dir.parent.parent}", file=sys.stderr)
                raise


def _do_import(db_path: Path, branch_dir: Path) -> tuple[str, dict]:
    """执行实际的 JSONL → SQLite 导入。"""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)

    # 事务保护：全部成功才提交，失败则回滚
    conn.execute("BEGIN TRANSACTION")

    # 清空现有数据
    for table in ["files", "modules", "commits", "commit_files", "nodes", "edges"]:
        conn.execute(f"DELETE FROM {table}")

    # 导入 files
    for f in _load_jsonl(branch_dir / "index" / "files.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                f.get("id"), f.get("path"), f.get("name"), f.get("role"),
                f.get("language"), f.get("size_bytes"), f.get("content_hash"),
                f.get("module_id"), json.dumps(f.get("symbols", [])),
                json.dumps(f.get("imports", [])), f.get("updated_at"),
            ),
        )

    # 导入 modules
    for m in _load_jsonl(branch_dir / "index" / "modules.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO modules VALUES (?,?,?,?,?,?)",
            (
                m.get("id"), m.get("name"), m.get("root_path"),
                m.get("file_count"), json.dumps(m.get("roles", [])),
                m.get("summary"),
            ),
        )

    # 导入 commits
    for c in _load_jsonl(branch_dir / "index" / "commits.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO commits VALUES (?,?,?,?,?,?,?,?)",
            (
                c.get("hash"), c.get("short_hash"), c.get("author"),
                c.get("date"), c.get("message"), c.get("files_changed"),
                c.get("insertions"), c.get("deletions"),
            ),
        )

    # 导入 commit_files
    for cf in _load_jsonl(branch_dir / "index" / "commit_files.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO commit_files VALUES (?,?,?)",
            (cf.get("commit_hash"), cf.get("file_path"), cf.get("change_type")),
        )

    # 导入 nodes
    for n in _load_jsonl(branch_dir / "graph" / "nodes.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?)",
            (
                n.get("id"), n.get("type"), n.get("name"),
                n.get("path"), n.get("summary"), json.dumps(n.get("meta", {})),
            ),
        )

    # 导入 edges
    for e in _load_jsonl(branch_dir / "graph" / "edges.jsonl"):
        conn.execute(
            "INSERT OR REPLACE INTO edges VALUES (?,?,?,?,?,?)",
            (
                e.get("from"), e.get("to"), e.get("type"),
                e.get("source"), e.get("confidence"), e.get("summary"),
            ),
        )

    conn.commit()

    # 统计
    counts = {}
    for table in ["files", "modules", "commits", "commit_files", "nodes", "edges"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()
    return str(db_path), counts


def query_files_by_module(db_path: str, module_id: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM files WHERE module_id = ?", (module_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_commits_for_file(db_path: str, file_path: str, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT c.* FROM commits c
        JOIN commit_files cf ON c.hash = cf.commit_hash
        WHERE cf.file_path = ?
        ORDER BY c.date DESC
        LIMIT ?
    """, (file_path, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_file_by_path(db_path: str, file_path: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM files WHERE path = ?", (file_path,)).fetchone()
    conn.close()
    return dict(row) if row else None
