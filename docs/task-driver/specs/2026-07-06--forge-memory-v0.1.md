# Forge Memory v0.1 Spec

**Date:** 2026-07-06
**Quality level:** Polished
**Status:** Approved

## Goal

实现 Forge Memory v0.1，作为 `project-memory` 的完整升级替代：吸收其全部能力（项目初始化、结构化扫描、Markdown 摘要、知识图谱、会话记忆），并新增 JSONL 静态索引、`content_hash` 增量扫描、上下文包生成、统一 CLI 和配套 Claude Code skill（替代 `project-memory` skill，实现自然触发）。

## User And Scenario

研发智能体需要在任务开始前快速建立项目认知。`forge-memory init` 初始化 `.project-context/`，`forge-memory scan` 生成完整项目上下文（人类可读摘要 + 机器可消费 JSONL 索引），二次扫描通过 `content_hash` 仅更新变更文件。`forge-memory context` 接收任务描述生成聚焦的上下文包，`forge-memory session` 管理会话记忆。

## Scope

### 迁移自 project-memory（吸收）

- `forge-memory init`：初始化 `.project-context/`，创建 `context.json`、`INDEX.md`、`project-summary.md`（占位）、`sessions/index.md`
- 结构化扫描：文件遍历、角色分类、符号提取、导入解析、包脚本提取、文档首段摘要、代码注释提取
- Markdown 摘要生成：`project-summary.md`（合并版，含项目概览、运行链路、核心 Contract、风险地图、Worktree 快照、Skill/Agent 专项、Mermaid 图谱）
- 知识图谱：`graph/nodes.jsonl`、`graph/edges.jsonl`、`graph/graph.md`、`graph/mermaid.md`
- 会话记忆：`forge-memory session add`（添加会话摘要）、`forge-memory session list`（列出会话）
- `scans/latest.json`（扫描摘要，非嵌入式文件列表）

### 新增 Forge Memory 独有

- `index/files.jsonl`：每文件一行，含 `content_hash`（sha256）、`id`、`path`、`role`、`language`、`size_bytes`、`module_id`、`symbols`、`imports`
- `index/modules.jsonl`：每模块一行，含 `id`、`name`、`root_path`、`file_count`、`roles`、`summary`
- `scans/history.jsonl`：每次扫描追加一行历史记录
- `content_hash` 增量扫描：二次扫描复用未变文件的记录，仅更新 `content_hash` 变化的文件
- `forge-memory status`：查看扫描状态（项目名、扫描时间、文件数、模块数、变更数）
- `forge-memory context --task "..." --entry <file>`：生成上下文包 `packs/latest-context-pack.md`（相关文件、模块、风险点、建议测试、置信度、caveat）
- `context.json` 升级：`schema_version: "forge-memory.static.v1"`, `generator: "forge-memory"`

### CLI 命令汇总

| 命令 | 来源 |
|---|---|
| `forge-memory init <root>` | 吸收 project-memory init_context.py |
| `forge-memory scan <root> [--force] [--backup] [--max-file-bytes N]` | 吸收 scan_project.py + 新增 JSONL/hash |
| `forge-memory status <root>` | 新增 |
| `forge-memory context <root> --task "..." [--entry <file>]` | 新增 |
| `forge-memory session add <root> --title "..." [--from-file <file>] [--allow-incomplete]` | 吸收 add_session.py |
| `forge-memory session list <root> [--json]` | 吸收 list_sessions.py |

### 配套 Claude Code skill（替代 project-memory skill）

forge-memory 仓库既是 CLI 工具又是 Claude Code skill，用户安装后 CLI 和自然触发一并就位。

| 文件 | 来源 |
|---|---|
| `SKILL.md` | 迁移自 project-memory SKILL.md + 调整触发规则指向 forge-memory CLI |
| `agents/openai.yaml` | 迁移自 project-memory agents/openai.yaml + 更新 display_name |
| `references/workflow.md` | 迁移自 project-memory references/workflow.md + 四状态选择器更新 |
| `references/schema.md` | 迁移自 project-memory references/schema.md + 补充 index/ 和 packs/ schema |

触发规则继承 project-memory 的两种触发方式，重命名为 `forge-memory`：
- 显式触发：用户写 `$forge-memory` 或说"使用 forge-memory"
- 被动触发：用户要求"全面了解/扫描/梳理项目"时可触发
- 四状态选择器：`总结会话摘要 > 读取会话记忆 > 读取项目结构化文件 > 初始化`
- 内部脚本改为调用 `forge_memory/` 包的统一入口

## Non-Goals

- 不做服务器、不做数据库、不做向量检索、不做后台监听、不做多人共享
- v0.1 不包含 MCP 接口（那是 v0.2）
- v0.1 不包含 Git 历史分析、`index/commits.jsonl`、`index/commit_files.jsonl`（那是 v0.3）
- v0.1 不包含 `index/chunks.jsonl`（那是 v0.5）
- v0.1 不包含 SQLite 存储（那是 v0.4）
- 不改变 `project-memory` 的 Markdown 摘要语义和四状态选择器约定

## Proposed Design

### 技术选型

Python 3，仅使用标准库（`json`、`hashlib`、`pathlib`、`argparse`、`os`、`re`、`subprocess`、`datetime` 等）。与 `project-memory` 执行环境一致，零外部依赖。

### 整体架构

```text
forge-memory/                     # 项目根目录（既是一个 Claude Code skill，也是 CLI 工具）
  SKILL.md                        # skill 入口（迁移自 project-memory SKILL.md）
  agents/
    openai.yaml                   # agent 元数据（迁移自 project-memory agents/openai.yaml）
  references/
    workflow.md                   # 四状态选择器 + 工作流（迁移自 project-memory references/workflow.md）
    schema.md                     # .project-context/ schema 定义（迁移+补充 index/、packs/）
  forge_memory.py                 # CLI 入口（argparse, 6 个子命令分发）
  forge_memory/
    __init__.py
    scanner.py                    # 文件遍历、分类、hash、符号/导入提取（迁移自 scan_project.py scan()）
    indexer.py                    # 读写 index/files.jsonl、index/modules.jsonl（新增）
    grapher.py                    # 读写 graph/*.jsonl、graph.md、mermaid.md（迁移+增强）
    renderer.py                   # Markdown 摘要渲染（迁移自 scan_project.py 全部 render_* 函数）
    context_pack.py               # 上下文包生成器（新增）
    session.py                    # 会话 add/list（迁移自 add_session.py + list_sessions.py）
    init.py                       # 初始化（迁移自 init_context.py）
    status.py                     # 状态查询（新增）
    utils.py                      # ID 生成、排除规则、路径工具、content_hash 计算（整合）
  docs/                           # 项目文档
  tests/                          # 测试（v0.1 为后续预留）
```

### content_hash 增量策略

```text
scan 命令:
  for each file in project:
    if index/files.jsonl 中已存在该 path 的记录:
      计算当前 content_hash
      if 与记录中一致:
        保留原记录（跳过）
      else:
        更新记录、symbols、imports、size_bytes
        标记 changed
    else:
      新建记录（新增文件）
  对 index/files.jsonl 中不再存在的 path:
    标记为已删除（从 index 移除）
  写入 scans/latest.json（含 changed_files、unchanged_files、new_files、deleted_files）
  追加 scans/history.jsonl
```

### 与 project-memory 的过渡

- forge-memory 首次 `scan` 时，自动将 `context.json` 升级为 `forge-memory.static.v1`
- 已由 `project-memory` 生成的 `project-summary.md`、`INDEX.md`、`sessions/` 会被安全覆盖（遵循 generated-marker 规则）
- 若需要保留旧版备份，用户使用 `--backup` 参数

## Alternatives Considered

- **保持 project-memory 和 forge-memory 并存**：维护两个工具会持续造成边界模糊和重复代码 → 选择直接吸收替代。
- **TypeScript/Node.js 实现**：可发布为 npm 包，但引入运行时依赖；Python 标准库零依赖，与现有生态一致 → 选择 Python。
- **init 和 scan 合并为一条命令**：简化 CLI 但失去了四状态选择器所需的"初始化 vs 扫描"语义 → 保留分开的命令，但 scan 在缺少 `.project-context/` 时会提示用户先 init。
- **skill 独立仓库**：CLI 工具和触发 skill 分两个仓库维护 → 选择集成到同一仓库，用户安装一个 skill 就全部就位。

## Acceptance Criteria

| ID | 验收项 | 验证方式 |
|---|---|---|
| AC-1 | `forge-memory init` 创建完整 `.project-context/` 目录结构，含 `context.json`、`INDEX.md`、`project-summary.md`、`sessions/index.md` | 在空 fixture 目录运行 init，检查所有文件存在且内容正确 |
| AC-2 | `forge-memory scan` 首次扫描产出 `project-summary.md`（含所有子章节）、`graph/nodes.jsonl`、`graph/edges.jsonl`、`graph/graph.md`、`graph/mermaid.md`、`scans/latest.json` | 在 fixture 项目上运行 scan，验证所有文件存在且格式正确 |
| AC-3 | `forge-memory scan` 产出 `index/files.jsonl`，每条记录包含 `id`、`path`、`role`、`language`、`size_bytes`、`content_hash`（sha256）、`module_id`、`symbols`、`imports` | 读取 `index/files.jsonl`，逐字段验证存在且类型正确 |
| AC-4 | `forge-memory scan` 产出 `index/modules.jsonl`，每条记录包含 `id`、`name`、`root_path`、`file_count`、`roles`、`summary` | 读取 `index/modules.jsonl`，验证字段完整性 |
| AC-5 | `forge-memory scan` 产出 `scans/history.jsonl`，每次扫描追加一行（含 scan_id、时间、文件数、变更数、状态） | 首次+二次扫描后检查 history.jsonl 有 2 行 |
| AC-6 | 二次扫描通过 `content_hash` 仅更新变化文件，`scans/latest.json` 中 `changed_files` 等于实际变更数 | 修改单个文件后重新 scan，验证 `changed_files=1` |
| AC-7 | `forge-memory status` 显示项目名、最后扫描时间、文件总数、模块数、变更文件数 | 在已扫描项目上运行 status，验证输出包含所有关键字段 |
| AC-8 | `forge-memory context --task "..."` 生成含所有必需章节的 `packs/latest-context-pack.md`：任务描述、相关文件、相关模块、风险点、建议测试、置信度、Caveats | 在 fixture 项目上运行 context 命令，检查输出 markdown 结构完整 |
| AC-9 | 置信度不足时上下文包包含 caveat 警告，不伪造事实 | 用模糊任务描述测试，验证输出含 caveat 且无不实断言 |
| AC-10 | `forge-memory session add --title "..."` 写入会话摘要到 `sessions/`，`session list` 能列出并包含该摘要 | 写入后 list 验证新摘要出现在列表中 |
| AC-11 | 排除构建产物目录和二进制/媒体文件类型（与 project-memory 排除规则一致） | 确认扫描结果不包含 `node_modules`、`.git`、`__pycache__`、图片等 |
| AC-12 | 覆盖 3 类 fixture：Python 项目（forge-memory 自身）、TypeScript CLI 项目（forge-cli）、Dart/Flutter 项目（flutter-forge） | 在 3 个项目上运行 scan 和 context，验证全部通过 |
| AC-13 | `SKILL.md` 存在且描述完整，包含触发规则（显式 + 被动）、四状态选择器、各状态执行步骤、脚本调用命令、必须遵守和暂停询问规则 | 读取 SKILL.md 验证结构和触发规则与 project-memory 一致且已重命名 |
| AC-14 | `references/workflow.md` 和 `references/schema.md` 存在且内容与 forge-memory CLI 命令一致（不再是 project-memory 的脚本路径） | 读取 references/ 验证脚本调用指向 forge_memory/ 而非 project-memory/ |
| AC-15 | skill 被动触发时能正确区分"全面了解项目"（进入状态 4 读取）和"全面扫描项目"（进入状态 1 初始化），与 project-memory 的四状态判定逻辑一致 | 模拟不同用户表述，验证触发路由正确 |

## Constraints

- Python 3 标准库，零外部依赖
- `.project-context/` 目录结构与 `static-store-schema.md` 一致
- `content_hash` 使用 sha256，对文件完整内容（截断至 `max_file_bytes`）计算
- 扫描单次完成，不做迭代循环
- 文件角色分类：`source`、`test`、`document`、`config`、`other`
- 模块归属按目录一级归类（与 project-memory 一致）
- 基于 `GENERATED_MARKER` 的安全覆盖规则：非生成文件必须 `--force` 才覆盖

## Risks

- **大项目扫描性能**：逐文件 sha256 在 10000+ 文件项目上可能耗时较长 → 缓解：记录扫描耗时，后续版本可加并发或缓存
- **语言支持有限**：符号提取和导入解析初期覆盖 TypeScript/JavaScript、Python、Dart/Go/Rust/Java 基础模式 → 缓解：在 context_pack 的 caveat 中明确标注语言覆盖范围
- **与 project-memory 过渡**：已安装的 project-memory 技能可能被同时调用 → 缓解：首次 scan 自动升级 context.json 的 generator 标记，project-memory 技能后续可标记为 deprecated

---

## SpecPacket

```yaml
spec_path: docs/task-driver/specs/2026-07-06--forge-memory-v0.1.md
goal: 实现 Forge Memory v0.1 作为 project-memory 的完整升级替代（CLI + skill）
user_scenario: 研发智能体通过自然触发或统一 CLI 管理项目上下文全生命周期
scope:
  - init：初始化 .project-context/（吸收 project-memory init_context.py）
  - scan：结构化扫描 + Markdown 摘要 + JSONL 索引 + content_hash 增量（吸收 scan_project.py + 新增）
  - status：扫描状态查看（新增）
  - context：任务级上下文包生成（新增）
  - session add/list：会话记忆管理（吸收 add_session.py + list_sessions.py）
  - SKILL.md + agents/ + references/：配套 skill 替代 project-memory skill，实现自然触发
non_goals:
  - 无服务器、无数据库、无 MCP、无 Git 历史分析、无向量检索
acceptance_criteria:
  - AC-1: init 创建完整目录结构
  - AC-2: scan 产出 Markdown 摘要和图谱
  - AC-3: scan 产出 index/files.jsonl 含 content_hash
  - AC-4: scan 产出 index/modules.jsonl
  - AC-5: scan 产出 scans/history.jsonl
  - AC-6: 二次扫描增量更新
  - AC-7: status 显示扫描状态
  - AC-8: context 生成完整上下文包
  - AC-9: 置信度不足输出 caveat
  - AC-10: session add/list 正常工作
  - AC-11: 排除规则正确
  - AC-12: 3 类 fixture 验证通过
  - AC-13: SKILL.md 触发规则完整
  - AC-14: references/ 内容与 CLI 一致
  - AC-15: 被动触发路由正确
constraints:
  - Python 3 标准库，零依赖
  - content_hash 使用 sha256
  - schema 与 static-store-schema.md 一致
risks:
  - 大项目扫描性能 / 语言支持有限 / 与 project-memory 过渡
quality_level: Polished
user_confirmed: false
```
