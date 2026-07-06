# Forge Memory v0.1 Implementation Plan

**Spec:** docs/task-driver/specs/2026-07-06--forge-memory-v0.1.md
**Ledger:** docs/task-driver/ledgers/2026-07-06--forge-memory-v0.1.md
**Mode:** single-agent
**Quality level:** Polished
**Status:** Approved
**Plan version:** v1
**Predecessor:** 无（首版）

## Change From Current State

forge-memory 当前只有 docs/ 和 README.md，无任何 Python 代码。这是对 project-memory（`/Users/agi00114/Desktop/AI/agent设计/project-memory/`）的全新升级替代。

结构性变化：
- 新增 `forge_memory.py` CLI 入口和 `forge_memory/` Python 包（8 个模块）
- 新增 `SKILL.md`、`agents/openai.yaml`、`references/workflow.md`、`references/schema.md`（从 project-memory 迁移并适配）
- 新增 `.project-context/` 下的 `index/`、`packs/` 子目录（Forge Memory 独有）
- `context.json` 的 `schema_version` 从 `1.0` 升级为 `forge-memory.static.v1`

保留项：
- project-memory 的排除规则、ID 生成逻辑、文件角色分类、模块归属规则、符号/导入提取模式
- project-memory 的四状态选择器、触发规则、generated-marker 安全覆盖机制
- `.project-context/` 目录约定和 Markdown 摘要语义

废弃项：
- project-memory 的独立脚本（`init_context.py`、`scan_project.py`、`add_session.py`、`list_sessions.py`）被 forge-memory 的 Python 包模块替代
- `scans/latest.json` 不再嵌入完整文件列表，改为紧凑摘要

## Goal

实现 Forge Memory v0.1 CLI 工具 + Claude Code skill，作为 project-memory 的完整升级替代。

## Global Constraints

- Python 3 标准库，零外部依赖
- `.project-context/` 目录结构与 `docs/static-store-schema.md` 一致
- `content_hash` 使用 sha256，对文件完整内容（截断至 `max_file_bytes`）计算
- 扫描单次完成，不做迭代循环
- 文件角色分类：`source`、`test`、`document`、`config`、`other`
- 模块归属按目录一级归类（与 project-memory 一致）
- 基于 `GENERATED_MARKER` 的安全覆盖规则：非生成文件必须 `--force` 才覆盖

## Assumptions

- **ASM-1**: project-memory 的 Python 脚本可作为迁移基础，无需从零编写核心扫描逻辑
  - 依据：project-memory/scripts/ 已有完整实现（init_context.py 165行、scan_project.py 1375行、add_session.py 118行、list_sessions.py 72行）
  - 验证点：T-002 迁移 init 时检查 project-memory init_context.py 逻辑完整性
  - 失效处理：若发现 project-memory 脚本有未文档化的隐含依赖，进入 blocked 并记录
  - 影响范围：T-001 到 T-007

- **ASM-2**: fixture 项目（forge-cli、flutter-forge）可被当前用户读取且含 `.project-context/` 或可初始化
  - 依据：之前已验证 `/Users/agi00114/Desktop/AI/agent设计/forge-cli/.project-context/` 存在
  - 验证点：T-010 验证阶段在 3 个项目上运行
  - 失效处理：若某 fixture 不可读，换一个同类项目替代
  - 影响范围：T-010、AC-12

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `forge_memory.py` | CLI 入口，argparse 6 个子命令分发 |
| Create | `forge_memory/__init__.py` | 包标识 |
| Create | `forge_memory/utils.py` | ID 生成、排除规则、路径工具、content_hash 计算 |
| Create | `forge_memory/init.py` | 初始化 .project-context/（迁移自 init_context.py） |
| Create | `forge_memory/scanner.py` | 文件遍历、分类、hash、符号/导入提取（迁移自 scan_project.py） |
| Create | `forge_memory/renderer.py` | Markdown 摘要渲染（迁移自 scan_project.py render_*） |
| Create | `forge_memory/grapher.py` | 图谱 nodes/edges JSONL + graph.md + mermaid.md |
| Create | `forge_memory/indexer.py` | index/files.jsonl + index/modules.jsonl 读写（新增） |
| Create | `forge_memory/session.py` | 会话 add/list（迁移自 add_session.py + list_sessions.py） |
| Create | `forge_memory/status.py` | 扫描状态查询（新增） |
| Create | `forge_memory/context_pack.py` | 任务级上下文包生成（新增） |
| Create | `SKILL.md` | skill 入口，触发规则（迁移自 project-memory SKILL.md） |
| Create | `agents/openai.yaml` | agent 元数据（迁移自 project-memory） |
| Create | `references/workflow.md` | 四状态选择器 + 工作流（迁移自 project-memory） |
| Create | `references/schema.md` | .project-context/ schema 定义（迁移+补充） |
| Create | `docs/task-driver/ledgers/2026-07-06--forge-memory-v0.1.md` | 执行台账 |

## Interfaces

### CLI 命令

```bash
# 初始化
python3 forge_memory.py init <project_root> [--allow-empty-root]

# 扫描
python3 forge_memory.py scan <project_root> [--force] [--backup] [--max-file-bytes N]

# 状态
python3 forge_memory.py status <project_root>

# 上下文包
python3 forge_memory.py context <project_root> --task "..." [--entry <file>]

# 会话
python3 forge_memory.py session add <project_root> --title "..." [--from-file <file>] [--allow-incomplete]
python3 forge_memory.py session list <project_root> [--json]
```

### Python 模块接口

```python
# forge_memory/utils.py
def stable_id(kind: str, key: str, name: str | None = None) -> str
def slugify(value: str, fallback: str = "item") -> str
def rel(path: Path, root: Path) -> str
def should_skip_file(path: Path) -> bool
def is_text_file(path: Path, max_bytes: int) -> bool
def read_text(path: Path, max_bytes: int) -> str
def content_hash(data: bytes) -> str  # sha256 hex
def now_iso() -> str

# forge_memory/init.py
def initialize(root: Path) -> list[Path]  # 返回创建的文件列表

# forge_memory/scanner.py
def scan(root: Path, max_file_bytes: int, existing_index: dict | None = None) -> dict
# 返回 {files, modules, nodes, edges, worktree, file_count, module_count, changed_files, ...}

# forge_memory/renderer.py
def render_full_summary(scan_result: dict) -> str
def render_project_overview(scan_result: dict) -> str
# ... 各 render_* 函数

# forge_memory/grapher.py
def write_graph(root: Path, scan_result: dict) -> None  # 写出 graph/*.jsonl, graph.md, mermaid.md

# forge_memory/indexer.py
def read_existing_index(context: Path) -> dict  # 读取已有 index/files.jsonl
def write_index(root: Path, scan_result: dict) -> None  # 写出 index/files.jsonl, index/modules.jsonl

# forge_memory/session.py
def add_session(root: Path, title: str, body: str, allow_incomplete: bool = False) -> str  # 返回 session_id
def list_sessions(root: Path) -> list[dict]

# forge_memory/status.py
def get_status(root: Path) -> dict  # 返回 {project_name, last_scan, file_count, module_count, changed_files}

# forge_memory/context_pack.py
def generate_context_pack(root: Path, task: str, entry_files: list[str] | None = None) -> str  # 返回 markdown
```

### 输出文件 Schema

```text
.context.json:
  schema_version: "forge-memory.static.v1"
  project_id: "proj-<slug>-<hash8>"
  project_root: "/absolute/path"
  created_at: "ISO-8601"
  updated_at: "ISO-8601"
  generator: "forge-memory"

.scans/latest.json:
  scan_id: "scan-YYYYMMDD-<hash6>"
  started_at: "ISO-8601"
  finished_at: "ISO-8601"
  status: "success" | "partial" | "error"
  file_count: int
  module_count: int
  changed_files: int
  unchanged_files: int
  new_files: int
  deleted_files: int
  errors: []

.scans/history.jsonl: 追加一行，结构同 latest.json

.index/files.jsonl: 每行 {id, path, name, role, language, size_bytes, content_hash, module_id, symbols, imports, updated_at}
.index/modules.jsonl: 每行 {id, name, root_path, file_count, roles, summary}

.packs/latest-context-pack.md: Markdown，含 Task / Likely Entry Files / Related Modules / Recent Changes / Dependency-Impact / Risk Points / Suggested Tests / Evidence And Caveats
```

## Tasks

### Task T-001: 包结构与工具模块

**Owner role:** Implementer
**Files:** `forge_memory/__init__.py`, `forge_memory/utils.py`
**Acceptance:** AC-11（排除规则正确）
**Review gate:** 规范合规 + 代码质量

- [ ] Step 1: 创建 `forge_memory/__init__.py`（空包标识）。
- [ ] Step 2: 在 `forge_memory/utils.py` 实现从 project-memory 迁移的工具函数：
  - `stable_id(kind, key, name)` — 使用 sha1，格式 `<kind>-<slug[:48]>-<hash8>`
  - `slugify(value, fallback)` — 小写字母数字+连字符
  - `rel(path, root)` — 相对路径 POSIX 格式
  - `should_skip_file(path)` — 检查 EXCLUDE_SUFFIXES
  - `is_text_file(path, max_bytes)` — 检查是否含 `\x00`
  - `read_text(path, max_bytes)` — 读取截断文本
  - `content_hash(data)` — sha256 hex digest
  - `now_iso()` — 当前时间 ISO-8601
  - 常量：`EXCLUDE_DIRS`、`EXCLUDE_SUFFIXES`、`CONFIG_NAMES`、`DOC_PATTERNS`、`LANG_BY_SUFFIX`、`ROLE_LABELS`、`GENERATED_MARKER`、`PLACEHOLDER_SNIPPETS`、`SYMBOL_PATTERNS`、`IMPORT_PATTERNS`、`PROJECT_SIGNAL_NAMES`、`PROJECT_SIGNAL_DIRS`
- [ ] Step 3: 运行 `python3 -c "from forge_memory.utils import stable_id, content_hash; print(stable_id('file', 'src/main.ts', 'main.ts')); print(content_hash(b'test'))"`。
      Expected: 输出类似 `file-src-main-ts-xxxxxxxx` 和 sha256 hex。
- [ ] Step 4: 写 TaskResult 到 ledger。
- [ ] Step 5: 写 ReviewReport 到 ledger。

### Task T-002: init 模块

**Owner role:** Implementer
**Files:** `forge_memory/init.py`
**Acceptance:** AC-1（init 创建完整目录结构）
**Review gate:** 规范合规 + 与 project-memory init_context.py 逻辑一致性

- [ ] Step 1: 迁移 `project-memory/scripts/init_context.py` 的 `initialize()` 函数到 `forge_memory/init.py`。
  - 保留 `has_project_signal()`、`write_if_missing()`、`generated_md()`
  - 升级 `schema_version` 为 `"forge-memory.static.v1"`
  - 升级 `generator` 为 `"forge-memory"`
  - 创建目录：`.project-context/`、`.project-context/sessions/`
  - 创建文件：`context.json`、`INDEX.md`、`project-summary.md`（占位）、`sessions/index.md`
  - INDEX.md 中的脚本路径改为 `forge_memory/` 而非 `project-memory/scripts/`
- [ ] Step 2: 运行 `python3 -c "from forge_memory.init import initialize; from pathlib import Path; import tempfile; t=Path(tempfile.mkdtemp()); print(initialize(t))"`。
      Expected: 输出创建的文件列表（4-5 个路径）。
- [ ] Step 3: 写 TaskResult 到 ledger。
- [ ] Step 4: 写 ReviewReport 到 ledger。

### Task T-003: scanner 模块

**Owner role:** Implementer
**Files:** `forge_memory/scanner.py`
**Acceptance:** AC-2（scan 产出摘要和图谱）、AC-3（index/files.jsonl 含 content_hash）、AC-4（index/modules.jsonl）、AC-11（排除规则）
**Review gate:** 规范合规 + 与 project-memory scan_project.py scan() 逻辑一致性 + content_hash 正确性

- [ ] Step 1: 迁移 `project-memory/scripts/scan_project.py` 的 `scan()` 函数到 `forge_memory/scanner.py`。
  - 保留：`classify_file()`、`module_key()`、`extract_symbols()`、`extract_imports()`、`extract_first_paragraph()`、`extract_code_comments()`、`extract_package_scripts()`、`extract_package_dependencies()`、`scan_worktree()`、`git_lines()`
  - 新增：`content_hash` 计算（对每个文件内容计算 sha256）
  - 新增：`existing_index` 参数支持（增量扫描时传入已有的 `index/files.jsonl` 数据）
  - `scan()` 返回值新增：`changed_files`、`unchanged_files`、`new_files`、`deleted_files`
  - 增量逻辑：遍历文件时，若 `existing_index` 中有同 path 记录且 `content_hash` 一致，保留原记录并标记 unchanged；否则标记 changed 或 new
- [ ] Step 2: 运行 `python3 -c "from forge_memory.scanner import scan; from pathlib import Path; r=scan(Path('/Users/agi00114/Desktop/AI/agent设计/forge-memory'), 200000); print(f'files={len(r[\"files\"])} modules={len(r[\"modules\"])} nodes={len(r[\"nodes\"])} edges={len(r[\"edges\"])}')"`。
      Expected: 输出合理的文件数和模块数（>0）。
- [ ] Step 3: 写 TaskResult 到 ledger。
- [ ] Step 4: 写 ReviewReport 到 ledger。

### Task T-004: renderer 模块

**Owner role:** Implementer
**Files:** `forge_memory/renderer.py`
**Acceptance:** AC-2（project-summary.md 含所有子章节）
**Review gate:** 规范合规 + Markdown 输出结构完整性

- [ ] Step 1: 迁移 `project-memory/scripts/scan_project.py` 的所有 `render_*` 函数到 `forge_memory/renderer.py`：
  - `render_full_summary()`、`render_project_overview()`、`render_runtime_flow_brief()`、`render_contracts_brief()`、`render_risk_map_brief()`、`render_worktree()`、`render_skill_summary_brief()`、`render_agent_summary_brief()`、`render_mermaid()`
  - 保留所有辅助函数：`find_contract_files()`、`find_runtime_files()`、`find_by_path()`、`is_skill_project()`、`is_agent_project()`、`source_modules_with_tests()`、`technology_signals()`、`role_counts()` 等
- [ ] Step 2: 运行 `python3 -c "from forge_memory.renderer import render_full_summary; from forge_memory.scanner import scan; from pathlib import Path; r=scan(Path('/Users/agi00114/Desktop/AI/agent设计/forge-memory'), 200000); s=render_full_summary(r); print(s[:500])"`。
      Expected: 输出 Markdown 格式的项目摘要开头（含 `# 项目摘要` 标题）。
- [ ] Step 3: 写 TaskResult 到 ledger。
- [ ] Step 4: 写 ReviewReport 到 ledger。

### Task T-005: grapher 模块

**Owner role:** Implementer
**Files:** `forge_memory/grapher.py`
**Acceptance:** AC-2（graph/nodes.jsonl、graph/edges.jsonl、graph/graph.md、graph/mermaid.md）
**Review gate:** 规范合规 + JSONL 格式正确性

- [ ] Step 1: 从 `project-memory/scripts/scan_project.py` 的 `write_outputs()` 中提取图谱写入逻辑到 `forge_memory/grapher.py`。
  - `write_graph(root, scan_result)` — 写出 `graph/nodes.jsonl`、`graph/edges.jsonl`、`graph/graph.md`、`graph/mermaid.md`
  - JSONL 使用 `write_jsonl()` 格式（每行一个 JSON，`sort_keys=True`）
  - `graph.md` 使用 `render_graph()` 内容
  - `mermaid.md` 使用 `render_mermaid()` 内容
- [ ] Step 2: 运行扫描后检查 `graph/` 目录文件。
      Expected: `graph/nodes.jsonl`、`graph/edges.jsonl`、`graph/graph.md`、`graph/mermaid.md` 均存在且非空。
- [ ] Step 3: 写 TaskResult 到 ledger。
- [ ] Step 4: 写 ReviewReport 到 ledger。

### Task T-006: indexer 模块

**Owner role:** Implementer
**Files:** `forge_memory/indexer.py`
**Acceptance:** AC-3（index/files.jsonl 含 content_hash）、AC-4（index/modules.jsonl）、AC-5（scans/history.jsonl）、AC-6（增量更新）
**Review gate:** 规范合规 + content_hash 一致性 + 增量逻辑正确性

- [ ] Step 1: 在 `forge_memory/indexer.py` 实现：
  - `read_existing_index(context: Path) -> dict` — 读取 `index/files.jsonl`，返回 `{path: record}` 字典
  - `write_index(root, scan_result)` — 写出 `index/files.jsonl` 和 `index/modules.jsonl`
  - `write_scan_summary(root, scan_result)` — 写出 `scans/latest.json` 和追加 `scans/history.jsonl`
  - `files.jsonl` 每行包含：`id`、`path`、`name`、`role`、`language`、`size_bytes`、`content_hash`、`module_id`、`symbols`、`imports`、`updated_at`
  - `modules.jsonl` 每行包含：`id`、`name`、`root_path`、`file_count`、`roles`、`summary`
  - `scans/latest.json` 包含：`scan_id`、`started_at`、`finished_at`、`status`、`file_count`、`module_count`、`changed_files`、`unchanged_files`、`new_files`、`deleted_files`、`errors`
  - 增量逻辑：`scan()` 传入 `existing_index` 后，输出的 `files` 列表中每条记录标记 `change_status`（`unchanged`/`changed`/`new`），`write_index` 只写出非 deleted 的记录
- [ ] Step 2: 运行完整 scan 流程后检查 `index/` 和 `scans/` 目录。
      Expected: `index/files.jsonl`、`index/modules.jsonl`、`scans/latest.json`、`scans/history.jsonl` 均存在且每条记录含必需字段。
- [ ] Step 3: 修改一个文件后重新 scan，验证 `scans/latest.json` 中 `changed_files >= 1`。
      Expected: `changed_files` 反映实际变更数。
- [ ] Step 4: 写 TaskResult 到 ledger。
- [ ] Step 5: 写 ReviewReport 到 ledger。

### Task T-007: session 模块

**Owner role:** Implementer
**Files:** `forge_memory/session.py`
**Acceptance:** AC-10（session add/list 正常工作）
**Review gate:** 规范合规 + 与 project-memory 脚本行为一致

- [ ] Step 1: 迁移 `project-memory/scripts/add_session.py` 和 `project-memory/scripts/list_sessions.py` 到 `forge_memory/session.py`。
  - `add_session(root, title, body, allow_incomplete=False) -> str` — 返回 session_id
  - `list_sessions(root) -> list[dict]` — 返回会话列表
  - 保留：`stable_session_id()`、`normalize_body()`、`validate_body()`、`update_index()`、`parse_frontmatter()`
- [ ] Step 2: 运行 `python3 -c "from forge_memory.session import list_sessions; from pathlib import Path; print(list_sessions(Path('/Users/agi00114/Desktop/AI/agent设计/forge-cli')))"`。
      Expected: 输出已有的会话列表（2 条记录）。
- [ ] Step 3: 写 TaskResult 到 ledger。
- [ ] Step 4: 写 ReviewReport 到 ledger。

### Task T-008: status 与 context_pack 模块

**Owner role:** Implementer
**Files:** `forge_memory/status.py`, `forge_memory/context_pack.py`
**Acceptance:** AC-7（status）、AC-8（context 上下文包）、AC-9（caveat）
**Review gate:** 规范合规 + 输出结构完整性 + caveat 逻辑

- [ ] Step 1: 在 `forge_memory/status.py` 实现 `get_status(root) -> dict`。
  - 读取 `scans/latest.json`，返回：`project_name`、`last_scan`、`file_count`、`module_count`、`changed_files`
  - 若 `scans/latest.json` 不存在，返回提示信息
- [ ] Step 2: 在 `forge_memory/context_pack.py` 实现 `generate_context_pack(root, task, entry_files=None) -> str`。
  - 读取 `index/files.jsonl` 和 `index/modules.jsonl`
  - 任务关键词匹配：从 task 提取关键词，匹配文件路径、模块名、符号名
  - 相关文件排序：入口文件优先 → 路径/符号匹配 → 同模块文件
  - 风险点识别：大文件（size_bytes > 50KB）、高导入文件（imports > 10）、无测试模块
  - 建议测试：相关模块中有源码但无测试的文件
  - 置信度评估：匹配文件数/关键词覆盖率 → `high`/`medium`/`low`
  - 置信度 low 时输出 caveat 段落
  - 输出 Markdown 格式：Task / Likely Entry Files / Related Modules / Recent Changes / Dependency-Impact / Risk Points / Suggested Tests / Evidence And Caveats
- [ ] Step 3: 运行 `python3 -c "from forge_memory.status import get_status; from pathlib import Path; print(get_status(Path('/Users/agi00114/Desktop/AI/agent设计/forge-cli')))"`。
      Expected: 输出包含 project_name、file_count 等字段的 dict。
- [ ] Step 4: 写 TaskResult 到 ledger。
- [ ] Step 5: 写 ReviewReport 到 ledger。

### Task T-009: CLI 入口与集成

**Owner role:** Implementer
**Files:** `forge_memory.py`
**Acceptance:** AC-1 到 AC-12 全部 CLI 可触发
**Review gate:** 规范合规 + 子命令路由正确 + 错误信息清晰

- [ ] Step 1: 在 `forge_memory.py` 实现 argparse CLI，6 个子命令：
  - `init` — 调用 `forge_memory.init.initialize(root, allow_empty_root)`
  - `scan` — 调用 `forge_memory.scanner.scan()` → `forge_memory.indexer.write_index()` + `forge_memory.indexer.write_scan_summary()` + `forge_memory.grapher.write_graph()` + `forge_memory.renderer.render_full_summary()` → 写 `project-summary.md`
  - `status` — 调用 `forge_memory.status.get_status()` → 格式化输出
  - `context` — 调用 `forge_memory.context_pack.generate_context_pack()` → 写 `packs/latest-context-pack.md`
  - `session add` — 调用 `forge_memory.session.add_session()`
  - `session list` — 调用 `forge_memory.session.list_sessions()`
  - `scan` 命令在缺少 `.project-context/` 时先自动调用 `initialize()`
- [ ] Step 2: 运行 `python3 forge_memory.py --help`。
      Expected: 显示 6 个子命令的帮助信息。
- [ ] Step 3: 运行 `python3 forge_memory.py init /tmp/test-fixture && python3 forge_memory.py scan /tmp/test-fixture`。
      Expected: init 和 scan 均成功，`.project-context/` 下产出所有预期文件。
- [ ] Step 4: 写 TaskResult 到 ledger。
- [ ] Step 5: 写 ReviewReport 到 ledger。

### Task T-010: skill 文件

**Owner role:** Implementer
**Files:** `SKILL.md`, `agents/openai.yaml`, `references/workflow.md`, `references/schema.md`
**Acceptance:** AC-13（SKILL.md 触发规则）、AC-14（references 与 CLI 一致）、AC-15（被动触发路由）
**Review gate:** 规范合规 + 触发规则完整性 + 脚本路径正确性

- [ ] Step 1: 从 project-memory 迁移并适配 `SKILL.md`：
  - `name: forge-memory`
  - `displayName: Forge Memory`
  - `description: 管理项目本地记忆 .project-context：初始化/扫描项目、读取结构化摘要、恢复会话记忆，并为 agent/skill 项目生成专项摘要和 JSONL 静态索引。`
  - 脚本命令改为 `python3 <forge-memory>/forge_memory.py <subcommand>`
  - 四状态选择器保持不变
- [ ] Step 2: 从 project-memory 迁移并适配 `agents/openai.yaml`：
  - `display_name: "Forge Memory"`
  - 更新 `default_prompt` 为 `使用 $forge-memory 初始化或恢复结构化项目上下文。`
- [ ] Step 3: 从 project-memory 迁移并适配 `references/workflow.md`：
  - 所有 `project-memory` 引用改为 `forge-memory`
  - 脚本路径改为 `python3 <forge-memory>/forge_memory.py <subcommand>`
  - 四状态判定逻辑保持不变
- [ ] Step 4: 从 project-memory 迁移并适配 `references/schema.md`：
  - 补充 `index/files.jsonl`、`index/modules.jsonl`、`scans/history.jsonl`、`packs/latest-context-pack.md` 的 schema 定义
  - `context.json` 的 `schema_version` 更新为 `forge-memory.static.v1`
- [ ] Step 5: 验证 `SKILL.md` 包含完整的触发规则、四状态选择器、各状态执行步骤。
      Expected: 读取 SKILL.md 确认结构完整。
- [ ] Step 6: 写 TaskResult 到 ledger。
- [ ] Step 7: 写 ReviewReport 到 ledger。

### Task T-011: 集成验证

**Owner role:** Verifier
**Files:** 无（纯验证）
**Acceptance:** AC-1 到 AC-15 全部覆盖
**Review gate:** 规范合规 + 3 类 fixture 验证

- [ ] Step 1: 在 forge-memory 自身（Python 项目）上运行完整流程：
  ```bash
  python3 forge_memory.py init /Users/agi00114/Desktop/AI/agent设计/forge-memory
  python3 forge_memory.py scan /Users/agi00114/Desktop/AI/agent设计/forge-memory
  python3 forge_memory.py status /Users/agi00114/Desktop/AI/agent设计/forge-memory
  python3 forge_memory.py context /Users/agi00114/Desktop/AI/agent设计/forge-memory --task "实现 content_hash 增量扫描"
  python3 forge_memory.py session list /Users/agi00114/Desktop/AI/agent设计/forge-memory
  ```
  Expected: 全部成功，产出完整 `.project-context/`，上下文包含相关文件。
- [ ] Step 2: 在 forge-cli（TypeScript CLI 项目）上运行：
  ```bash
  python3 forge_memory.py scan /Users/agi00114/Desktop/AI/agent设计/forge-cli
  python3 forge_memory.py context /Users/agi00114/Desktop/AI/agent设计/forge-cli --task "修复 multilineinput 粘贴问题"
  ```
  Expected: 扫描成功（兼容已有的 project-memory 产出），上下文包含相关文件。
- [ ] Step 3: 在 flutter-forge（Dart/Flutter 项目，若可访问）上运行：
  ```bash
  python3 forge_memory.py scan /Users/agi00114/Desktop/AI/agent设计/flutter-forge
  python3 forge_memory.py context /Users/agi00114/Desktop/AI/agent设计/flutter-forge --task "修改订阅管理入口"
  ```
  Expected: 扫描成功，Dart 文件被正确分类。
- [ ] Step 4: 验证增量扫描：修改一个文件后重新 scan，检查 `changed_files`。
      Expected: `changed_files` 反映实际变更数。
- [ ] Step 5: 写 TaskResult 到 ledger。
- [ ] Step 6: 写 ReviewReport 到 ledger。
- [ ] Step 7: 写 VerificationReport 到 ledger。

## Verification Plan

| 命令 | 预期结果 | 覆盖 AC | evidence_strength |
|---|---|---|---|
| `python3 forge_memory.py init /tmp/test-fixture` | 创建完整 `.project-context/` | AC-1 | strong |
| `python3 forge_memory.py scan /tmp/test-fixture` | 产出所有索引和摘要文件 | AC-2,3,4,5,11 | strong |
| 二次 scan 后检查 `scans/latest.json` | `changed_files` 正确 | AC-6 | strong |
| `python3 forge_memory.py status /tmp/test-fixture` | 输出含关键字段 | AC-7 | strong |
| `python3 forge_memory.py context /tmp/test-fixture --task "..."` | 输出完整上下文包 | AC-8,9 | strong |
| `python3 forge_memory.py session add/list` | 会话写入和列出正常 | AC-10 | strong |
| 在 3 类 fixture 上运行 scan+context | 全部成功 | AC-12 | strong |
| 读取 SKILL.md、references/ | 结构完整、路径正确 | AC-13,14,15 | strong |

## Stop Conditions

- 任何任务的验证命令失败且 2 轮修复后仍失败 → 进入 blocked
- project-memory 脚本有未文档化的隐含依赖导致迁移失败 → 记录到 ledger，评估是否需要从零编写
- fixture 项目不可读或被锁定 → 换同类项目替代
- scan 在 30 秒内无法完成 forge-memory 自身扫描 → 记录性能问题，不阻塞 v0.1

## PlanPacket

```yaml
plan_path: docs/task-driver/plans/2026-07-06--forge-memory-v0.1.md
ledger_path: docs/task-driver/ledgers/2026-07-06--forge-memory-v0.1.md
plan_version: v1
predecessor: 无
mode: single-agent
tasks:
  - id: T-001
    owner_role: Implementer
    objective: 包结构与工具模块（utils.py）
    files: [forge_memory/__init__.py, forge_memory/utils.py]
    verification: python3 -c "from forge_memory.utils import stable_id, content_hash; ..."
    acceptance_ac_ids: [AC-11]
  - id: T-002
    owner_role: Implementer
    objective: init 模块（迁移 init_context.py）
    files: [forge_memory/init.py]
    verification: python3 -c "from forge_memory.init import initialize; ..."
    acceptance_ac_ids: [AC-1]
  - id: T-003
    owner_role: Implementer
    objective: scanner 模块（迁移 scan_project.py scan() + content_hash）
    files: [forge_memory/scanner.py]
    verification: python3 -c "from forge_memory.scanner import scan; ..."
    acceptance_ac_ids: [AC-2, AC-3, AC-4, AC-11]
  - id: T-004
    owner_role: Implementer
    objective: renderer 模块（迁移 render_* 函数）
    files: [forge_memory/renderer.py]
    verification: python3 -c "from forge_memory.renderer import render_full_summary; ..."
    acceptance_ac_ids: [AC-2]
  - id: T-005
    owner_role: Implementer
    objective: grapher 模块（图谱 JSONL + graph.md + mermaid.md）
    files: [forge_memory/grapher.py]
    verification: 检查 graph/ 目录文件存在且非空
    acceptance_ac_ids: [AC-2]
  - id: T-006
    owner_role: Implementer
    objective: indexer 模块（index/files.jsonl + modules.jsonl + scans/）
    files: [forge_memory/indexer.py]
    verification: 检查 index/ 和 scans/ 目录文件含必需字段
    acceptance_ac_ids: [AC-3, AC-4, AC-5, AC-6]
  - id: T-007
    owner_role: Implementer
    objective: session 模块（迁移 add_session.py + list_sessions.py）
    files: [forge_memory/session.py]
    verification: python3 -c "from forge_memory.session import list_sessions; ..."
    acceptance_ac_ids: [AC-10]
  - id: T-008
    owner_role: Implementer
    objective: status 与 context_pack 模块
    files: [forge_memory/status.py, forge_memory/context_pack.py]
    verification: python3 -c "from forge_memory.status import get_status; ..."
    acceptance_ac_ids: [AC-7, AC-8, AC-9]
  - id: T-009
    owner_role: Implementer
    objective: CLI 入口（argparse 6 个子命令）
    files: [forge_memory.py]
    verification: python3 forge_memory.py --help
    acceptance_ac_ids: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12]
  - id: T-010
    owner_role: Implementer
    objective: skill 文件（SKILL.md + agents/ + references/）
    files: [SKILL.md, agents/openai.yaml, references/workflow.md, references/schema.md]
    verification: 读取 SKILL.md 确认结构完整
    acceptance_ac_ids: [AC-13, AC-14, AC-15]
  - id: T-011
    owner_role: Verifier
    objective: 集成验证（3 类 fixture + 增量扫描）
    files: []
    verification: 在 3 个项目上运行完整流程
    acceptance_ac_ids: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12, AC-13, AC-14, AC-15]
stop_conditions:
  - 任何任务验证命令 2 轮修复后仍失败
  - project-memory 脚本有未文档化的隐含依赖导致迁移失败
  - fixture 项目不可读且无替代
status: draft
```
