# Forge Memory v0.2 + v0.3 Implementation Plan

**Spec:** docs/task-driver/specs/2026-07-06--branch-isolation-and-git-memory.md
**Ledger:** docs/task-driver/ledgers/2026-07-06--branch-isolation-and-git-memory.md
**Mode:** single-agent
**Quality level:** Polished
**Status:** Approved
**Plan version:** v1
**Predecessor:** 无

## Goal

让 forge-memory 支持分支隔离存储和 Git 历史分析。

## Global Constraints

- Python 标准库 + sqlite3，零外部依赖
- 不改变现有 CLI 命令的参数签名（新增参数为可选）
- 迁移自动执行，不需要用户手动操作
- SQLite 为可选后端，JSONL 保持默认
- 验证项目：`/Users/agi00114/Desktop/flutter项目/facesong_flutter`

## File Map

- Modify: `forge_memory/utils.py` — 添加分支路径解析、git 辅助函数
- Modify: `forge_memory/init.py` — 创建 branches/<branch>/ 结构、context.json 加 active_branch
- Modify: `forge_memory/scanner.py` — 旧结构迁移逻辑、调用 git_history
- Modify: `forge_memory/indexer.py` — 写入 branches/<branch>/ 子目录
- Modify: `forge_memory/grapher.py` — 写入 branches/<branch>/ 子目录
- Modify: `forge_memory/status.py` — 显示分支信息和 commit 统计
- Modify: `forge_memory/context_pack.py` — 读取分支子目录数据
- Modify: `forge_memory/renderer.py` — 渲染 commit 历史摘要
- Modify: `forge_memory/session.py` — sessions 保持全局（无需大改）
- Modify: `forge_memory.py` — 添加 impact、import-db 命令
- Create: `forge_memory/git_history.py` — git log 解析、commits.jsonl、commit_files.jsonl
- Create: `forge_memory/impact.py` — 影响分析逻辑
- Create: `forge_memory/sqlite_backend.py` — SQLite 后端
- Modify: `docs/roadmap.md` — 更新 v0.2/v0.3 状态

## Interfaces

### 新增函数

```python
# utils.py
def current_branch(root: Path) -> str:
    """返回当前 git 分支名，非 git 仓库返回 'default'。"""

def branch_context_path(root: Path, branch: str) -> Path:
    """返回 .project-context/branches/<branch>/ 路径。"""

def sanitize_branch_name(branch: str) -> str:
    """将分支名转为安全目录名（/ → _）。"""

# git_history.py
def scan_git_history(root: Path, max_commits: int = 50) -> dict:
    """解析 git log，返回 {commits: [...], commit_files: [...]}。"""

def load_existing_commits(context: Path) -> list[dict]:
    """读取已有 commits.jsonl。"""

def append_new_commits(context: Path, commits: list[dict], commit_files: list[dict]) -> int:
    """增量追加新 commit，返回新增数量。"""

def is_git_stale(context: Path, root: Path) -> bool:
    """比对 commits.jsonl 最新 hash 与 HEAD。"""

# impact.py
def analyze_impact(root: Path, file_path: str, context: Path) -> dict:
    """分析文件影响：导入关系、同模块文件、近期 commit、风险信号。"""

# sqlite_backend.py
def import_jsonl_to_sqlite(context: Path, branch: str) -> str:
    """将 JSONL 数据导入 SQLite，返回 .db 文件路径。"""

def query_from_sqlite(db_path: str, query_type: str, params: dict) -> dict:
    """从 SQLite 查询数据。"""
```

### 新增 CLI 命令

```bash
forge-memory impact <project-root> <file-path> [--backend jsonl|sqlite]
forge-memory import-db <project-root> [--branch <branch>]
forge-memory context <project-root> --task "..." [--backend jsonl|sqlite]  # 新增 --backend
forge-memory scan <project-root> [...]  # 行为变化：自动检测分支、写入子目录
```

## Tasks

### Task T-001: 分支路径工具函数
**Owner role:** Implementer
**Files:** `forge_memory/utils.py`
**Acceptance:** AC-3（context.json 含 active_branch 的基础）
**Review gate:** 函数签名正确、sanitize 处理边界

- [ ] Step 1: 在 `utils.py` 添加 `current_branch(root)` 函数，调用 `git branch --show-current`，非 git 仓库返回 `"default"`。
- [ ] Step 2: 添加 `sanitize_branch_name(branch)` 函数，将 `/` 替换为 `_`，限制长度 64 字符。
- [ ] Step 3: 添加 `branch_context_path(root, branch)` 函数，返回 `root / ".project-context" / "branches" / sanitize(branch)`。
- [ ] Step 4: 手动验证：在 facesong_flutter 运行 `python3 -c "from forge_memory.utils import current_branch; print(current_branch('/Users/agi00114/Desktop/flutter项目/facesong_flutter'))"`。
      Expected: 输出 `dev-ohos`。

### Task T-002: 目录重构 + 迁移
**Owner role:** Implementer
**Files:** `forge_memory/init.py`, `forge_memory/scanner.py`
**Acceptance:** AC-1, AC-2, AC-3, AC-4
**Review gate:** 迁移不丢数据、旧目录清理干净

- [ ] Step 1: 修改 `init.py` 的 `initialize()`，创建 `branches/` 目录，在 `context.json` 中写入 `active_branch` 字段（调用 `current_branch`）。
- [ ] Step 2: 在 `scanner.py` 的 `scan()` 函数开头添加迁移逻辑：如果检测到 `.project-context/index/` 存在（旧结构），将其移动到 `branches/<current-branch>/index/`，同理 `graph/` 和 `scans/`。
- [ ] Step 3: 修改 `indexer.py` 的 `write_index()` 和 `write_scan_summary()`，路径从 `root / ".project-context" / "index"` 改为 `branch_context_path(root, branch) / "index"`。添加 `branch` 参数。
- [ ] Step 4: 修改 `grapher.py` 的 `write_graph()`，同理改为分支子目录路径。添加 `branch` 参数。
- [ ] Step 5: 修改 `forge_memory.py` 的 `cmd_scan()`，传递 branch 参数给 `write_index`、`write_scan_summary`、`write_graph`。更新 `context.json` 的 `active_branch`。
- [ ] Step 6: 在 facesong_flutter 运行 `python3 /Users/agi00114/Desktop/AI/agent设计/forge-memory/forge_memory.py scan /Users/agi00114/Desktop/flutter项目/facesong_flutter --force`。
      Expected: 索引写入 `branches/dev-ohos/`，旧 `index/` 目录不存在。
- [ ] Step 7: 写 TaskResult + ReviewReport 到 ledger。

### Task T-003: Git 历史扫描
**Owner role:** Implementer
**Files:** `forge_memory/git_history.py`（新建）, `forge_memory/scanner.py`
**Acceptance:** AC-5, AC-6
**Review gate:** commit 数量正确、文件列表完整

- [ ] Step 1: 创建 `git_history.py`，实现 `scan_git_history(root, max_commits=50)`。使用 `subprocess` 调用 `git log -50 --format="%H|%h|%an|%ai|%s" --numstat` 解析 commit 信息和文件变更。
- [ ] Step 2: 实现 `load_existing_commits(context)` 读取已有 `commits.jsonl`。
- [ ] Step 3: 实现 `append_new_commits(context, commits, commit_files)`，比对 hash 后只追加新记录。
- [ ] Step 4: 实现 `is_git_stale(context, root)`，比对最新 commit hash 与 `git rev-parse HEAD`。
- [ ] Step 5: 在 `scanner.py` 的 `scan()` 结束时调用 `scan_git_history`，将结果合并到 scan_result。在 `forge_memory.py` 的 `cmd_scan()` 中调用 `append_new_commits` 写入分支子目录。
- [ ] Step 6: 在 facesong_flutter 运行 scan，检查 `branches/dev-ohos/index/commits.jsonl`。
      Expected: 包含 commit 记录，行数 ≤ 50，每行含 hash/author/date/message。
- [ ] Step 7: 抽查 3 个 commit 对比 `git show --stat <hash>`。
      Expected: commit_files.jsonl 中的文件列表与 git show 一致。
- [ ] Step 8: 写 TaskResult + ReviewReport 到 ledger。

### Task T-004: impact 命令
**Owner role:** Implementer
**Files:** `forge_memory/impact.py`（新建）, `forge_memory.py`
**Acceptance:** AC-7, AC-8, AC-9
**Review gate:** 输出格式正确、风险信号有依据

- [ ] Step 1: 创建 `impact.py`，实现 `analyze_impact(root, file_path, context)`。从 `files.jsonl` 读取导入关系，从 `modules.jsonl` 找同模块文件，从 `commits.jsonl` + `commit_files.jsonl` 找近期 commit。
- [ ] Step 2: 风险信号逻辑：高频变更（该文件在 commits 中出现 ≥ 5 次）、缺少测试（未找到对应 test 文件）。
- [ ] Step 3: 建议测试逻辑：将 `lib/pages/x/y.dart` 映射为 `test/pages/x/y_test.dart`。
- [ ] Step 4: 在 `forge_memory.py` 添加 `impact` 子命令：`forge-memory impact <project-root> <file-path> [--backend jsonl|sqlite]`。
- [ ] Step 5: 实现过期检测：如果 `is_git_stale` 为 true，自动更新 commits.jsonl 再分析。
- [ ] Step 6: 在 facesong_flutter 运行 `python3 forge_memory.py impact /Users/agi00114/Desktop/flutter项目/facesong_flutter lib/pages/share/share_page.dart`。
      Expected: 输出包含导入关系、同模块文件、近期 commit、风险信号。
- [ ] Step 7: 写 TaskResult + ReviewReport 到 ledger。

### Task T-005: SQLite 后端
**Owner role:** Implementer
**Files:** `forge_memory/sqlite_backend.py`（新建）, `forge_memory.py`
**Acceptance:** AC-10, AC-11
**Review gate:** 表结构正确、查询结果与 JSONL 一致

- [ ] Step 1: 创建 `sqlite_backend.py`，实现 `import_jsonl_to_sqlite(context, branch)`。创建 6 张表（files, modules, commits, commit_files, nodes, edges），从 JSONL 导入数据。
- [ ] Step 2: 实现 `query_from_sqlite(db_path, query_type, params)`，支持按 path 查 files、按 module 查 files、按 file 查 commits。
- [ ] Step 3: 在 `forge_memory.py` 添加 `import-db` 子命令。
- [ ] Step 4: 修改 `cmd_context` 和 `cmd_impact` 添加 `--backend` 参数，sqlite 模式从 .db 查询。
- [ ] Step 5: 在 facesong_flutter 运行 `python3 forge_memory.py import-db /Users/agi00114/Desktop/flutter项目/facesong_flutter`。
      Expected: `.project-context/branches/dev-ohos/forge-memory.db` 存在，表有数据。
- [ ] Step 6: 对比 `--backend jsonl` 和 `--backend sqlite` 的 context 输出。
      Expected: 内容一致。
- [ ] Step 7: 写 TaskResult + ReviewReport 到 ledger。

### Task T-006: status 更新 + 渲染
**Owner role:** Implementer
**Files:** `forge_memory/status.py`, `forge_memory/renderer.py`
**Acceptance:** AC-12
**Review gate:** 输出包含分支名

- [ ] Step 1: 修改 `status.py` 的 `get_status()`，从 `context.json` 读取 `active_branch`，从分支子目录读取 `latest.json`。添加 `branch` 和 `commit_count` 字段。
- [ ] Step 2: 修改 `renderer.py` 的 `render_full_summary()`，添加 commit 历史摘要段落。
- [ ] Step 3: 修改 `context_pack.py` 的 `generate_context_pack()`，从分支子目录读取数据，移除"v0.1 不包含 Git 历史分析"的 caveat。
- [ ] Step 4: 在 facesong_flutter 运行 `python3 forge_memory.py status /Users/agi00114/Desktop/flutter项目/facesong_flutter`。
      Expected: 输出包含 `分支：dev-ohos` 和 commit 统计。
- [ ] Step 5: 写 TaskResult + ReviewReport 到 ledger。

### Task T-007: 集成验证
**Owner role:** Verifier
**Files:** 无（只运行命令）
**Acceptance:** AC-1 ~ AC-12 全部覆盖
**Review gate:** 所有 AC 标 met 或 partial

- [ ] Step 1: 在 facesong_flutter dev-ohos 分支运行完整流程：`scan → status → context → impact → import-db`。
- [ ] Step 2: 验证 AC-1：检查 `branches/dev-ohos/index/files.jsonl` 存在。
- [ ] Step 3: 验证 AC-2：记录 dev-ohos 索引 hash，切 main 分支 scan，再检查 dev-ohos 索引未变。
- [ ] Step 4: 验证 AC-3：读取 context.json 确认 active_branch。
- [ ] Step 5: 验证 AC-4~12：逐条运行验证命令。
- [ ] Step 6: 写 VerificationReport 到 ledger。

## Verification Plan

| 验证命令 | 预期结果 | 覆盖 AC |
|---|---|---|
| `python3 forge_memory.py scan <facesong> --force` | 索引写入 branches/dev-ohos/ | AC-1, AC-3 |
| 检查 branches/dev-ohos/index/files.jsonl 存在 | 文件存在且有内容 | AC-1 |
| 切 main 分支 scan 后检查 dev-ohos 索引 | 文件仍存在且 hash 不变 | AC-2 |
| 读取 context.json | 含 active_branch 字段 | AC-3 |
| 检查旧 index/ 目录 | 不存在 | AC-4 |
| `wc -l branches/dev-ohos/index/commits.jsonl` | 行数 ≤ 50 | AC-5 |
| `git show --stat <hash>` 对比 | 文件列表一致 | AC-6 |
| `python3 forge_memory.py impact <facesong> lib/pages/share/share_page.dart` | 输出含 commit hash | AC-7 |
| impact 输出检查 | 含导入文件 | AC-8 |
| impact 输出检查 | 含风险标记 | AC-9 |
| `python3 forge_memory.py import-db <facesong>` | .db 文件有数据 | AC-10 |
| 对比 jsonl/sqlite context 输出 | 内容一致 | AC-11 |
| `python3 forge_memory.py status <facesong>` | 含分支名 | AC-12 |

## Stop Conditions

- 迁移逻辑导致现有索引数据丢失 → 立即停止，恢复备份
- git log 解析在 facesong_flutter 上超时 30 秒 → 减少 max_commits 或优化解析
- SQLite 导入后数据行数与 JSONL 不一致 → 停止排查映射逻辑
- impact 命令输出格式与 spec 不符 → 调整输出格式

## Assumptions

- **ASM-1**: facesong_flutter 的 git log 可用且有足够 commit。依据：已验证 `git log --oneline -10` 有输出。验证点：T-003 Step 6。失效处理：减少 max_commits 或标记 blocked。
- **ASM-2**: `git log --numstat` 格式在 macOS git 上稳定。依据：标准 git 功能。验证点：T-003 Step 1。失效处理：改用 `git show --stat` 逐 commit 解析。
- **ASM-3**: sqlite3 模块在目标 Python 版本可用。依据：Python 3.x 标准库内置。验证点：T-005 Step 1。失效处理：记录 blocked，建议安装 sqlite3。
