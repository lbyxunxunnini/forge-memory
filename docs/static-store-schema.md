# Static Store Schema

Forge Memory 第一版使用项目内静态存储。目录固定在被扫描项目根目录下：

```text
.project-context/
  context.json
  project-summary.md
  scans/
    latest.json
    history.jsonl
  index/
    files.jsonl
    modules.jsonl
    commits.jsonl
    commit_files.jsonl
    chunks.jsonl
  graph/
    nodes.jsonl
    edges.jsonl
    graph.md
    mermaid.md
  packs/
    latest-context-pack.md
  sessions/
    index.md
```

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

`latest.json` 是最近一次扫描摘要，不复制完整源码。

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
  "errors": []
}
```

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

必须包含：

- `path`
- `role`
- `language`
- `size_bytes`
- `content_hash`
- `module_id`

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

## index/commits.jsonl

v0.2 开始写入。

```json
{
  "hash": "abc123",
  "author": "name",
  "date": "2026-07-06T10:00:00+08:00",
  "message": "fix: update context pack",
  "summary": "Updated context pack generation."
}
```

## index/commit_files.jsonl

v0.2 开始写入。

```json
{
  "commit_hash": "abc123",
  "file_path": "src/context.ts",
  "change_type": "modified"
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

## graph/edges.jsonl

```json
{
  "from": "mod-src-agent-51a9c771",
  "to": "file-src-agent-loop-ts-12345678",
  "type": "contains",
  "source": "rule",
  "confidence": "high",
  "summary": "Module contains file."
}
```

关系类型第一版只需要：

- `contains`
- `defines`
- `imports`
- `belongs_to_module`

后续再扩展：

- `modifies`
- `documents`
- `affects`
- `summarizes`

## packs/latest-context-pack.md

保存最近一次上下文包，便于调试和复现。

上下文包不得伪造事实。确定性事实和推断建议必须分区展示。
