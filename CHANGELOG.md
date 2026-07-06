# Changelog

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
