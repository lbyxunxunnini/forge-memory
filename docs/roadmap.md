# Forge Memory Roadmap

**日期：** 2026-07-06
**质量层级：** 精打磨
**存储策略：** 静态优先，按需引入 SQLite

## 总体目标

Forge Memory 的目标不是做普通知识库，而是做研发智能体可消费的项目上下文基础设施。

```text
用户任务
  -> Forge Memory 生成项目上下文包
  -> task-driver 计划阶段消费上下文包
  -> 智能体精准读取源码、制定计划、执行和验证
```

## 与 project-memory 的关系

`project-memory` 是起点，不是终点。

| 维度 | project-memory 当前能力 | Forge Memory 目标 |
|---|---|---|
| 核心用途 | 生成 `.project-context/` 摘要和会话记忆 | 提供任务级上下文检索和影响分析 |
| 存储方式 | Markdown 摘要为主 | JSONL 静态索引优先，后续可选 SQLite |
| 查询方式 | 读取 `project-summary.md` | CLI/MCP 返回聚焦的 `context_pack` |
| 增量能力 | 不完整 | `content_hash`、变更文件、扫描状态 |
| Git 记忆 | worktree 快照 | commit 历史、文件变更图、模块近期变化 |
| 图关系 | 有 schema 意图 | 可查询的文件、模块、导入、关系 |
| 智能体集成 | 手动触发技能 | 任务驱动框架计划阶段自动消费 |

可复用资产：

- `.project-context/` 目录约定。
- 文档和构建产物排除规则。
- 稳定 ID 设计。
- 文件角色分类、模块启发式、符号和导入提取。
- worktree 快照和用户改动提醒。
- 会话摘要机制。

必须补齐：

- 结构化索引落盘。
- `content_hash` 增量扫描。
- 面向任务的上下文包生成。
- CLI 和 MCP 接口。
- 任务驱动框架集成。
- fixture、golden case 和降级路径验证。

## 版本路线

### v0.1 静态智能体上下文存储 (已完成)

目标：

```text
把 project-memory 升级为结构化静态索引生成器，并能按任务生成上下文包。
```

交付物：

- `.project-context/scans/latest.json`
- `.project-context/scans/history.jsonl`
- `.project-context/index/files.jsonl`
- `.project-context/index/modules.jsonl`
- `.project-context/graph/nodes.jsonl`
- `.project-context/graph/edges.jsonl`
- 文件级 `content_hash`
- `forge-memory scan`
- `forge-memory status`
- `forge-memory context`

非目标：

- 不做服务器。
- 不做数据库。
- 不做向量检索。
- 不做后台监听。
- 不做多人共享。

验收：

- 首次扫描能创建完整静态索引。
- 二次扫描只更新 `content_hash` 变化的文件。
- 输入任务后能返回相关文件、模块、风险点、建议验证范围和 `context_pack`。
- 置信度不足时必须输出 caveat。
- 至少覆盖 3 类 fixture：小型技能项目、TypeScript CLI/智能体项目、Flutter 或 H5 项目。

### v0.2 Git 记忆与影响分析 (已完成)

目标：

```text
支持分支隔离存储，增加项目历史和第一版影响分析。
```

交付物：

- 目录重构：`.project-context/branches/<branch>/` 每个分支独立存储
- 旧结构自动迁移到当前分支子目录
- `index/commits.jsonl`（per-branch，追加式，最近 50 commit）
- `index/commit_files.jsonl`（per-branch）
- `forge-memory impact` 命令
- 风险排序信号：高频变更、缺少测试
- context pack 自动包含近期 commit

验收：

- 扫描不同分支不覆盖彼此索引。
- 输入文件路径后返回直接导入、同模块文件、近期 commit 和建议测试。
- 输入任务后上下文包包含相关近期变更。

### v0.3 可选 SQLite 索引 (已完成)

目标：

```text
只有静态索引证明价值后，才引入本地数据库。
```

交付物：

- 本地 SQLite 存储。
- JSONL 到 SQLite 的导入器。
- 与静态模式一致的 CLI 契约。
- 从静态存储迁移的路径。
- JSONL 与 SQLite 的查询性能对比。

验收：

- 同一命令在静态模式和 SQLite 模式下行为一致。
- JSONL 仍保留为可调试、可导出的格式。
- 查询性能在万级文件项目上有可感知提升。

### v0.4 任务驱动框架集成

目标：

```text
让 task-driver 在计划阶段先消费 Forge Memory 上下文，再生成计划。
```

交付物：

- MCP 工具 `forge_memory_get_context`。
- 任务驱动框架计划阶段规则。
- Forge Memory 不可用时的降级路径。
- 上下文检索证据写入执行台账的格式。
- 示例计划展示上下文包如何影响文件映射和验证范围。

验收：

- 计划阶段记录已调用 `forge_memory_get_context`。
- 计划中的相关文件和建议测试来自上下文包。
- Forge Memory 不可用时明确记录降级，不伪装成已使用上下文。

### v0.5 检索质量和轻量 RAG

目标：

```text
提升上下文相关性，但保持来源可追溯。
```

交付物：

- 文档、摘要、决策和关键代码注释的 chunk metadata。
- 词法检索优先。
- embedding 适配器作为可选开关。
- 每个 chunk 都有来源路径、hash 和范围信息。
- 基于 `content_hash` 的过期检测。

非目标：

- 不粗暴向量化完整源码树。

验收：

- 检索结果包含来源路径、hash、行或章节范围。
- 过期 chunk 被排除或明确标记。
- `context_pack` 不把无证据推断写成事实。

### v0.6 可选本地 API

目标：

```text
只有 CLI 启动成本、多项目路由或后台同步成为真实瓶颈时，才增加本地服务。
```

交付物：

- 本地 Fastify API 或同等服务。
- `/agent/context`
- `/sync/local-repo`
- `/impact/analyze`
- `/files/search`
- health/status endpoint。

验收：

- MCP 可以调用 CLI 或本地 API。
- 服务模式可选。
- 静态模式继续可用。

### v1.0 精打磨本地智能体上下文基础设施

目标：

```text
交付一个能证明平台工程能力的本地上下文基础设施。
```

必须具备：

- 静态存储稳定可用。
- CLI 命令稳定，错误信息清楚。
- MCP 能被任务驱动框架消费。
- 计划阶段使用 `context_pack`。
- Git 历史和影响分析在真实项目上有用。
- 验证覆盖 scan、rescan、context、impact、降级路径和 fixture。
- 文档能解释 before/after 工作流。

v1.0 不是云平台，而是精打磨的本地平台组件。

## 里程碑

| 里程碑 | 输出 | 证明方式 |
|---|---|---|
| M1 | 对齐 `project-memory` 输出 | 写出 JSONL 和 `scans/latest.json` |
| M2 | Forge Memory CLI 雏形 | `scan/status/context` 能跑 fixture |
| M3 | 上下文包生成器 | golden context pack 测试通过 |
| M4 | Git 和影响分析 | 文件影响包含关系和近期变更 |
| M5 | SQLite 可选索引 | 静态和 SQLite 模式行为一致 |
| M6 | 任务驱动框架集成 | 计划展示来自上下文包的文件映射 |
| M7 | 精打磨发布 | 文档、示例、错误、降级路径、测试齐全 |

## 数据收集门

这些不是当前文档的阻塞项，但实施前应该闭合。

| 数据门 | 阻塞阶段 | 需要的数据 | 推荐默认值 |
|---|---|---|---|
| DC-1 首个 demo 项目 | v0.1 fixture 质量 | 选择一个真实项目 | 用 `project-memory` 和一个智能体/CLI 项目 |
| DC-2 语言优先级 | v0.2 关系准确性 | 先强化哪门语言 | TypeScript 优先，再 Dart/Flutter |
| DC-3 存储偏好 | v0.3 | SQLite 是否真的需要 | JSONL 不够用时再加 |
| DC-4 宿主集成 | v0.4 MCP 细节 | 哪个宿主先消费 MCP | 先接任务驱动框架 |
| DC-5 隐私边界 | v1.0 精打磨 | 索引是否允许保存片段 | 限制摘要和片段大小 |

实施前第一个真正需要拍板的问题是：选择首个真实 demo 仓库。
