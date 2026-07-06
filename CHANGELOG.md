# Changelog

## v0.3.1 (2026-07-06)

触发与文档优化。

### 变更
- SKILL.md description 重写：覆盖更多自动触发场景（项目全貌、上下文包、影响分析、会话恢复、索引扫描、任务驱动框架）
- 新增 `项目说明.md`：项目背景、安装教程、使用说明、可优化项、推进方向、未完成内容
- 修复 impact 命令依赖匹配 bug（空文件名导致 `.env` 误匹配）

## v0.3.0 (2026-07-06)

SQLite 索引后端。

### 新增
- `import-db` 命令：JSONL → SQLite 导入
- SQLite 表结构：files, modules, commits, commit_files, nodes, edges
- SQLite 查询接口：按路径查文件、按模块查文件、按文件查 commit
- `forge-memory.db` 存储在分支子目录下

### 验证
- facesong_flutter 导入验证：2263 files, 28 modules, 50 commits, 249 commit_files, 4950 nodes, 11481 edges
- SQLite 查询结果与 JSONL 一致

## v0.2.0 (2026-07-06)

分支隔离存储与 Git 记忆。

### 新增
- 目录重构：`.project-context/branches/<分支名>/` 每个分支独立存储
- 旧结构自动迁移到当前分支子目录
- Git commit 历史扫描：`commits.jsonl`（per-branch，追加式，最近 50 个）
- commit 文件列表：`commit_files.jsonl`
- `impact` 命令：文件影响分析（导入关系、同模块文件、近期 commit、风险信号）
- 过期检测：impact 自动检测新 commit 并更新
- `status` 命令显示当前分支和 commit 统计
- `context` 包自动包含相关近期 commit

### 变更
- `context.json` 新增 `active_branch` 字段
- `indexer.py`、`grapher.py` 支持 `branch_dir` 参数
- `context_pack.py` 从分支子目录读取数据

### 验证
- facesong_flutter 分支切换验证：dev-ohos（2263 文件）→ main（1685 文件），索引互不覆盖
- impact 命令在 share_util.dart 上验证通过
- commit 增量追加验证：二次 scan 新增 0 个

## v0.1.0 (2026-07-06)

首次发布。作为 project-memory 的完整升级替代。

### 新增
- CLI 工具 `forge_memory.py`，支持 6 个子命令：init / scan / status / context / session add / session list
- `content_hash`（sha256）增量扫描：二次扫描只更新变化文件
- 任务级上下文包生成：根据任务描述匹配相关文件、风险点、建议测试
- 中文→英文术语映射：支持中文任务描述匹配英文代码文件
- JSONL 静态索引：`index/files.jsonl`、`index/modules.jsonl`
- 知识图谱：`graph/nodes.jsonl`、`graph/edges.jsonl`
- 扫描历史：`scans/history.jsonl`
- Claude Code skill（SKILL.md），支持自然触发和四状态选择器
- 排除规则：.git / node_modules / build / .trae / .cxx 等

### 迁移自 project-memory
- 项目初始化（init_context.py → forge_memory/init.py）
- 结构化扫描（scan_project.py → forge_memory/scanner.py + renderer.py）
- 会话记忆管理（add_session.py + list_sessions.py → forge_memory/session.py）
- Markdown 摘要生成、知识图谱、Worktree 快照

### 验证
- 在 4 个项目上验证通过：forge-memory（Python）、forge-cli（TypeScript）、flutter-forge（Dart）、facesong_flutter（Flutter，3000+ 文件）
