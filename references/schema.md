# 项目上下文 Schema

本文件定义 Forge Memory 创建的 `.project-context/` 目录结构。

## 目录结构

```text
.project-context/
  context.json           # 元数据（含 active_branch）
  INDEX.md               # 入口索引
  project-summary.md     # 项目全貌（一个文件包含所有内容）
  branches/<分支名>/
    index/
      files.jsonl        # 文件索引（每文件一行，含 content_hash）
      modules.jsonl      # 模块索引（每模块一行）
      commits.jsonl      # 提交历史
      commit_files.jsonl # 提交文件关联
    graph/
      nodes.jsonl        # 图节点
      edges.jsonl        # 图关系
      graph.md           # 人类可读图谱摘要
      mermaid.md         # Mermaid 可视化骨架
    scans/
      latest.json        # 最近一次扫描摘要
      history.jsonl      # 扫描历史（每次扫描追加一行）
    packs/
      latest-context-pack.md  # 最近一次上下文包
    forge-memory.db      # SQLite 索引（可选）
  sessions/
    index.md             # 会话摘要索引
    YYYY-MM-DD__session-id__title-slug.md
```

## doctor 输出

`forge_memory.py doctor <project-root>` 输出两组检查结果和总结。

```json
{
  "environment": [
    {
      "name": "Python 版本",
      "status": "ok",
      "value": "3.12.0",
      "message": ""
    },
    {
      "name": "Git",
      "status": "ok",
      "value": "git version 2.44.0",
      "message": ""
    }
  ],
  "index": [
    {
      "name": "context.json",
      "status": "ok",
      "value": "分支: main",
      "message": ""
    },
    {
      "name": "project-summary.md",
      "status": "ok",
      "value": "2048 bytes",
      "message": ""
    },
    {
      "name": "files.jsonl",
      "status": "ok",
      "value": "240 个文件",
      "message": ""
    },
    {
      "name": "forge-memory.db",
      "status": "info",
      "value": "不存在",
      "message": "可选：运行 import-db 创建"
    }
  ],
  "summary": {
    "errors": 0,
    "warnings": 0
  }
}
```

status 取值：`ok`（正常）、`warning`（警告，不影响核心功能）、`error`（错误，需修复）、`info`（信息性提示）

## context.json

```json
{
  "schema_version": "forge-memory.static.v1",
  "project_id": "proj-name-hash",
  "project_root": "/absolute/path",
  "created_at": "2026-07-06T10:00:00+08:00",
  "updated_at": "2026-07-06T10:10:00+08:00",
  "generator": "forge-memory"
}
```

## scans/latest.json

```json
{
  "scan_id": "scan-20260706-abc123",
  "started_at": "2026-07-06T10:00:00+08:00",
  "finished_at": "2026-07-06T10:00:12+08:00",
  "status": "success",
  "file_count": 240,
  "module_count": 18,
  "changed_files": 3,
  "unchanged_files": 237,
  "new_files": 0,
  "deleted_files": 0,
  "errors": []
}
```

## scans/history.jsonl

每次扫描追加一行，结构同 `latest.json`。

## index/files.jsonl

每行一个文件实体。

```json
{
  "id": "file-src-main-ts-0d5c12aa",
  "path": "src/main.ts",
  "name": "main.ts",
  "role": "source",
  "language": "typescript",
  "size_bytes": 1234,
  "content_hash": "sha256:...",
  "module_id": "mod-src-51a9c771",
  "symbols": ["main"],
  "imports": ["./app"],
  "updated_at": "2026-07-06T10:00:00+08:00"
}
```

## index/modules.jsonl

每行一个模块或目录区域。

```json
{
  "id": "mod-src-agent-51a9c771",
  "name": "src/agent",
  "root_path": "src/agent",
  "file_count": 12,
  "roles": ["source", "test"],
  "summary": "Agent loop and orchestration files."
}
```

## graph/nodes.jsonl

```json
{
  "id": "file-src-main-ts-0d5c12aa",
  "type": "file",
  "name": "main.ts",
  "path": "src/main.ts",
  "summary": "Application entry.",
  "meta": {
    "language": "typescript",
    "content_hash": "sha256:..."
  }
}
```

节点类型：`project`、`directory`、`module`、`file`、`symbol`、`document`、`config`

## graph/edges.jsonl

```json
{
  "from": "mod-src-agent-51a9c771",
  "to": "file-src-agent-loop-ts-12345678",
  "type": "contains",
  "summary": "Module contains file.",
  "meta": {}
}
```

关系类型：`contains`、`defines`、`imports`、`references`、`documents`、`configures`

## packs/latest-context-pack.md

上下文包 Markdown，含以下章节：

- Task
- Likely Entry Files
- Related Modules
- Recent Changes
- Dependency / Impact
- Risk Points
- Suggested Tests
- Evidence And Caveats

## 会话摘要格式

```markdown
---
id: sess-20260706-example-a1b2c3d4
title: 示例会话
date: 2026-07-06
created_at: 2026-07-06T10:00:00+08:00
---

# 示例会话

日期：2026-07-06
会话 ID：sess-20260706-example-a1b2c3d4

## 摘要

...

## 决策

...

## 已变更或重要文件

...

## 未决问题

...

## 下一步

...
```

## ID 规则

格式：`<kind>-<slug>-<hash8>`

类型前缀：
- `proj`：项目
- `dir`：目录
- `file`：文件
- `mod`：模块或包区域
- `sym`：类、函数、组件、命令或导出符号

哈希输入使用稳定逻辑键（通常是相对路径）。文件实体统一使用 `file-*`。

示例：
```text
file-src-main-ts-0d5c12aa
mod-src-api-51a9c771
sym-src-main-ts-app-23e91b9e
```
