# Forge Memory v0.2 + v0.3 Spec

**Date:** 2026-07-06
**Quality level:** Polished
**Status:** Approved

## Goal

让 forge-memory 支持分支隔离存储和 Git 历史分析，使多分支项目的上下文不再互相覆盖，并能基于 commit 历史做影响分析。

## User And Scenario

智能体开发者在多分支项目（如 facesong_flutter 的 dev-ohos / main）上工作时，需要：
- 在不同分支扫描不覆盖彼此的索引
- 查看当前分支的 commit 历史和文件变更
- 输入文件路径后获得影响分析（近期变更、导入关系、风险信号）

## Scope

### v0.2 分支隔离 + Git 记忆

- 目录重构：`.project-context/branches/<branch>/` 每个分支独立存储
- context.json 记录 active_branch
- 扫描自动检测当前分支，写入对应子目录
- 旧结构自动迁移到当前分支子目录
- commits.jsonl：最近 50 个 commit（per-branch）
- commit_files.jsonl：每个 commit 涉及的文件（per-branch）
- `forge-memory impact <file-path>` 命令
- impact 输出：直接导入、同模块文件、近期 commit、风险信号、建议测试
- `forge-memory status` 显示当前分支信息

### v0.3 SQLite 索引

- 本地 SQLite 存储后端
- JSONL → SQLite 导入命令：`forge-memory import-db`
- CLI `--backend sqlite` 参数切换查询后端
- 同一命令在 JSONL 和 SQLite 模式下行为一致
- JSONL 保留为可调试、可导出格式

## Non-Goals

- 不做向量检索或 embedding
- 不做后台监听或自动同步
- 不做多人共享或远程服务
- 不做跨分支影响分析（只分析当前分支历史）
- 不做 SQLite 自动同步（需要手动 import-db）

## Proposed Design

### 目录结构（v0.2）

```text
.project-context/
  context.json           # 新增 active_branch 字段
  project-summary.md     # 全局摘要（渲染当前分支）
  branches/
    main/
      index/
        files.jsonl
        modules.jsonl
        commits.jsonl        # v0.2 新增
        commit_files.jsonl   # v0.2 新增
      graph/
        nodes.jsonl
        edges.jsonl
      scans/
        latest.json
        history.jsonl
      packs/
        latest-context-pack.md
    dev-ohos/
      index/
        ...
      graph/
        ...
      scans/
        ...
      packs/
        ...
  sessions/              # 全局共享
    index.md
```

### context.json 变更

```json
{
  "schema_version": "forge-memory.static.v1",
  "project_id": "proj-facesong-flutter-6af721e6",
  "project_root": "/path/to/project",
  "active_branch": "dev-ohos",
  "created_at": "...",
  "updated_at": "...",
  "generator": "forge-memory"
}
```

### 分支检测与迁移

scan 命令流程：

1. 运行 `git branch --show-current` 获取当前分支
2. 检查 context.json 的 active_branch
3. 如果 `.project-context/index/` 存在（旧结构），自动迁移到 `branches/<current-branch>/`
4. 写入当前分支的索引目录
5. 更新 context.json 的 active_branch

### 更新机制

触发方式：仅手动命令或大模型调用，无后台进程、无文件监听、无自动同步。

| 触发点 | 行为 | 说明 |
|---|---|---|
| `scan` | 自动更新 commits.jsonl | 和文件扫描同生命周期，增量追加新 commit |
| `impact` | 检测过期则自动刷新 | 对比 commits.jsonl 最新 hash 与 HEAD，不同则先更新再分析 |
| `context` | 不触发 | 只读取已有数据 |

过期检测方式：比对 commits.jsonl 最新记录的 hash 与 `git rev-parse HEAD`。

commits.jsonl 采用追加式更新：每次 scan 只追加新 commit，不删除旧的。50 是 `git log -50` 的查询深度，不是总量上限。

### commits.jsonl 格式

```json
{
  "hash": "a5b44806925ad0c1b8cebe1fb51c4b4bb87c926d",
  "short_hash": "a5b44806",
  "author": "name",
  "date": "2026-07-06T10:00:00+08:00",
  "message": "feat(ohos): Day 1 分享降级策略 + 系统分享适配",
  "files_changed": 3,
  "insertions": 45,
  "deletions": 12
}
```

### commit_files.jsonl 格式

```json
{
  "commit_hash": "a5b44806925ad0c1b8cebe1fb51c4b4bb87c926d",
  "file_path": "lib/pages/share/share_page.dart",
  "change_type": "modified"
}
```

### impact 命令

```bash
forge-memory impact <project-root> <file-path>
```

输出（JSON + 终端友好格式）：

```text
=== Impact Analysis: lib/pages/share/share_page.dart ===

直接导入:
- lib/utils/share_utils.dart
- lib/pages/home/home_page.dart

同模块文件 (lib/pages/share/):
- lib/pages/share/share_config.dart
- lib/pages/share/share_reward_dialog.dart

近期 Commit (最近 5 个涉及该文件):
- a5b44806 2026-07-06 feat(ohos): Day 1 分享降级策略 + 系统分享适配
- 207f2426 2026-07-05 feat: add isAllModelFree parameter

风险信号:
- 高频变更: 该文件近 50 commit 中被修改 8 次
- 缺少测试: 未找到对应的 test 文件

建议测试:
- test/pages/share_page_test.dart
```

### SQLite 后端（v0.3）

表结构（镜像 JSONL）：

```sql
CREATE TABLE files (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  name TEXT,
  role TEXT,
  language TEXT,
  size_bytes INTEGER,
  content_hash TEXT,
  module_id TEXT,
  symbols TEXT,  -- JSON array
  imports TEXT,  -- JSON array
  updated_at TEXT
);

CREATE TABLE modules (
  id TEXT PRIMARY KEY,
  name TEXT,
  root_path TEXT,
  file_count INTEGER,
  roles TEXT,  -- JSON array
  summary TEXT
);

CREATE TABLE commits (
  hash TEXT PRIMARY KEY,
  short_hash TEXT,
  author TEXT,
  date TEXT,
  message TEXT,
  files_changed INTEGER,
  insertions INTEGER,
  deletions INTEGER
);

CREATE TABLE commit_files (
  commit_hash TEXT,
  file_path TEXT,
  change_type TEXT,
  PRIMARY KEY (commit_hash, file_path)
);

CREATE TABLE nodes (
  id TEXT PRIMARY KEY,
  type TEXT,
  name TEXT,
  path TEXT,
  summary TEXT,
  meta TEXT  -- JSON
);

CREATE TABLE edges (
  from_id TEXT,
  to_id TEXT,
  type TEXT,
  source TEXT,
  confidence TEXT,
  summary TEXT,
  PRIMARY KEY (from_id, to_id, type)
);
```

导入命令：

```bash
forge-memory import-db <project-root> [--branch <branch>]
```

查询后端切换：

```bash
forge-memory context <project-root> --task "..." --backend sqlite
forge-memory impact <project-root> <file-path> --backend sqlite
```

## Alternatives Considered

- **全局共享索引 + branch 字段标记**：查询时需要过滤，增加复杂度，不如目录隔离直观。拒绝。
- **SQLite 作为默认后端**：v0.1 用户已有 JSONL 工作流，强制迁移成本高。改为可选后端。接受折中。
- **全量 commit 历史**：大仓库扫描慢，50 个 commit 覆盖一个迭代周期足够。拒绝。

## Acceptance Criteria

| ID | 验收项 | 验证方式 |
|---|---|---|
| AC-1 | 扫描 facesong_flutter 的 dev-ohos 分支后，索引写入 `branches/dev-ohos/` | 检查文件路径存在 |
| AC-2 | 切换到 main 分支扫描，dev-ohos 索引不被覆盖 | 检查 `branches/dev-ohos/index/files.jsonl` 仍存在且内容不变 |
| AC-3 | context.json 包含正确的 active_branch | 读取 JSON 验证 |
| AC-4 | 旧结构自动迁移到当前分支子目录 | 初始化后检查旧 `index/` 目录不存在，新 `branches/<branch>/index/` 存在 |
| AC-5 | commits.jsonl 包含最近 50 个 commit（或分支不足 50 个时全部） | 检查行数和内容 |
| AC-6 | commit_files.jsonl 每个 commit 涉及的文件列表完整 | 抽查 3 个 commit 对比 `git show` |
| AC-7 | impact 命令对 lib/pages/share/ 下文件返回近期 commit | 运行命令检查输出包含 commit hash |
| AC-8 | impact 命令返回导入关系 | 检查输出包含直接导入文件 |
| AC-9 | impact 命令返回风险信号（高频变更、缺少测试） | 检查输出包含风险标记 |
| AC-10 | import-db 将 JSONL 数据导入 SQLite | 运行后检查 .db 文件存在且表有数据 |
| AC-11 | --backend sqlite 的 context 命令输出与 JSONL 一致 | 对比两种后端的 context pack 内容 |
| AC-12 | status 命令显示当前分支 | 运行 status 检查输出包含分支名 |

## Constraints

- Python 标准库 + sqlite3（内置），零外部依赖
- 不改变现有 CLI 命令的参数签名（新增参数为可选）
- 迁移为自动执行，不需要用户手动操作
- SQLite 为可选后端，JSONL 保持默认

## Risks

- **迁移失败**：旧结构文件损坏时迁移可能出错。缓解：迁移前备份，失败时保留旧结构。
- **大仓库 commit 解析慢**：50 个 commit 的 `git show` 解析可能耗时。缓解：限制深度，使用 `git log --stat` 一次性获取。
- **SQLite 与 JSONL 数据不一致**：import-db 后如果重新 scan，SQLite 数据过期。缓解：import-db 时记录时间戳，status 提示过期。

## SpecPacket

```yaml
spec_path: docs/task-driver/specs/2026-07-06--branch-isolation-and-git-memory.md
goal: 让 forge-memory 支持分支隔离存储和 Git 历史分析
acceptance_criteria:
  - {id: AC-1, description: 扫描 dev-ohos 分支后索引写入 branches/dev-ohos/, verification: 检查文件路径}
  - {id: AC-2, description: 切换 main 分支扫描不覆盖 dev-ohos 索引, verification: 检查 files.jsonl 仍存在}
  - {id: AC-3, description: context.json 包含 active_branch, verification: 读取 JSON}
  - {id: AC-4, description: 旧结构自动迁移, verification: 检查目录结构}
  - {id: AC-5, description: commits.jsonl 包含最近 50 commit, verification: 检查行数}
  - {id: AC-6, description: commit_files.jsonl 文件列表完整, verification: 抽查对比 git show}
  - {id: AC-7, description: impact 返回近期 commit, verification: 运行命令}
  - {id: AC-8, description: impact 返回导入关系, verification: 检查输出}
  - {id: AC-9, description: impact 返回风险信号, verification: 检查输出}
  - {id: AC-10, description: import-db 导入 SQLite, verification: 检查 .db 文件}
  - {id: AC-11, description: --backend sqlite 输出与 JSONL 一致, verification: 对比输出}
  - {id: AC-12, description: status 显示当前分支, verification: 运行 status}
constraints:
  - Python 标准库 + sqlite3 零外部依赖
  - 不改变现有 CLI 参数签名
  - 迁移自动执行
  - SQLite 为可选后端
quality_level: polished
approved_by_user: true
status: approved
```
