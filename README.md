# Forge Memory

GitHub: lbyxunxunnini/forge-memory · License: MIT · 当前版本：**v0.3.1**

Forge Memory 是面向研发智能体的本地项目记忆层。不做服务器、不做后台进程，用本地静态索引和 SQLite 把”项目全貌、文件事实、Git 历史、影响分析、上下文包”稳定提供给任务驱动框架和其他智能体。

核心目标：

```text
让 task-driver 在计划阶段先拿到项目上下文包，再生成文件映射、风险点和验证范围。
```

## 定位

Forge Memory 不是单个技能，也不是某个智能体的私有记忆。推荐边界是：

```text
用户级运行入口
  -> 项目级静态记忆与索引
  -> 智能体级上下文接口
```

当前版本支持分支隔离存储和 Git 历史：

```text
.project-context/
  context.json           # 含 active_branch
  project-summary.md
  branches/<分支名>/
    index/*.jsonl        # files, modules, commits, commit_files
    graph/*.jsonl        # nodes, edges
    scans/*.json
    packs/*.md
    forge-memory.db      # SQLite（可选）
  sessions/
```

## 为什么先静态版

静态版足够验证最关键的产品价值：

- 项目扫描能稳定生成结构化事实。
- 二次扫描能基于 `content_hash` 识别变化。
- 智能体能按任务拿到相关文件、模块、风险点和建议验证范围。
- 任务驱动框架可以在计划阶段使用上下文包，而不是从零盲扫项目。

服务器、数据库、后台同步和轻量 RAG 都是后续增强项，只有静态版证明价值后再进入。

## 文档索引

- [项目说明](项目说明.md) — 背景、安装、使用说明、优化项、推进方向
- [路线图](docs/roadmap.md)
- [静态存储结构](docs/static-store-schema.md)
- [任务驱动集成](docs/task-driver-integration.md)
- [转型差距评估](docs/transition-gap.md)

## 第一阶段建议

先完成两个里程碑：

```text
M1: 对齐 project-memory 输出，补齐 JSONL 和 content_hash。
M2: 增加 forge-memory scan/status/context CLI。
```

完成这两个里程碑后，再接入任务驱动框架的计划阶段。
