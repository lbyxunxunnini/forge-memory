# Forge Memory

GitHub: lbyxunxunnini/forge-memory · License: MIT · 当前版本：**v0.4.4**

Forge Memory 是面向研发智能体的本地项目记忆层。不做服务器、不做后台进程，用本地静态索引和 SQLite 把”项目全貌、文件事实、Git 历史、影响分析、上下文包”稳定提供给智能体。

核心目标：

```text
让智能体在执行任务前先拿到项目上下文包，再精准读取源码、制定计划、执行和验证。
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

## 5 分钟快速开始

```bash
# 1. 克隆项目
git clone https://github.com/lbyxunxunnini/forge-memory.git

# 2. 初始化项目记忆（在你的项目根目录运行）
python3 /path/to/forge-memory/forge_memory.py init ./your-project

# 3. 扫描项目（生成索引和知识图谱）
python3 /path/to/forge-memory/forge_memory.py scan ./your-project

# 4. 生成任务上下文包（按任务描述匹配相关文件）
python3 /path/to/forge-memory/forge_memory.py context ./your-project --task "你的任务描述"
```

完成这 3 个命令后，你就能拿到项目的结构化上下文包，智能体可以直接基于它精准读取源码、制定计划。

更多命令和用法见 [项目说明](项目说明.md)。

## 文档索引

- [项目说明](项目说明.md) — 背景、安装、使用说明、FAQ、推进方向
- [路线图](docs/roadmap.md)
- [静态存储结构](docs/static-store-schema.md)
- [评分提升计划](docs/评分提升计划.md)
- [转型差距评估](docs/transition-gap.md)

## 第一阶段建议

先完成两个里程碑：

```text
M1: 对齐 project-memory 输出，补齐 JSONL 和 content_hash。
M2: 增加 forge-memory scan/status/context CLI。
```

完成这两个里程碑后，再接入任务驱动框架的计划阶段。
