# Changelog

## v0.4.6 (2026-07-07)

索引能力增强：中文关键词索引、TODO/FIXME 索引、Skill 类型文件识别。

### 新增
- 中文关键词索引：从源码字符串字面量提取中文，用于中文意图定位代码模块
- TODO/FIXME 索引：提取代码中的 TODO/FIXME/HACK/NOTE 注释，带行号
- Skill 类型识别：SKILL.md、references/、agents/ 被识别为 skill 类型，提取中文段落关键词
- `extract_chinese_keywords`、`extract_todos`、`extract_skill_keywords` 三个新函数

### 修复
- 修复 `shutil` import 缺失
- 修复 `classify_file` 传入绝对路径导致 skill 目录匹配失败

## v0.4.5 (2026-07-07)

触发规则升级为三级：完整触发、被动读取、不触发。局部任务时被动读取 project-summary.md 加速代码定位。

### 改进
- 触发纪律从二级扩展为三级，新增"被动读取"层级
- 局部 bug 排查、模块修改等任务先读 project-summary.md 定位模块，再定向读源码
- frontmatter description 同步更新触发规则描述

## v0.4.4 (2026-07-07)

扫描噪声治理：统一排除所有 `.` 开头目录，补全 Flutter/HarmonyOS 生态目录，初始化扫描后增加噪声置信度排查。

### 改进
- 统一排除所有 `.` 开头目录（不再逐个枚举）
- 补全 EXCLUDE_DIRS：oh_modules、.hvigor、.ohpm、.fvm、.pub-cache、.fleet
- 初始化扫描后自动执行噪声置信度排查，输出疑似噪声目录和清理建议

## v0.4.3 (2026-07-07)

发布到 SkillHub，包含 v0.4.1-v0.4.2 全部改进。

### 新增
- 上下文包质量评分：基于覆盖率/新鲜度/Hash 覆盖率的 A/B/C/D 评分
- 会话恢复异常处理：文件损坏、摘要过时、index 不一致的检测和回退路径
- doctor 输出 schema：定义 doctor 命令的 JSON 输出结构
- 核心操作退出条件表：init/scan/context/import-db 的异常退出和降级策略
- status 命令质量评分：C/D 时输出重新扫描建议
- SKILL.md Mermaid 架构流程图

### 变更
- SKILL.md 自动触发条件细化和授权机制明确化
- schema.md 目录结构更新为分支隔离布局
- workflow.md 触发前提与 SKILL.md 对齐
- SKILL.md 脚本部分补充 doctor 命令
- SKILL.md 验证章节增加质量评分检查步骤
- 项目说明.md CLI 章节引用 SKILL.md 避免重复维护
- 评分提升计划切换到三方评估法 14 维度

## v0.4.2 (2026-07-07)

P2 改进：退出条件、质量评分闭环、架构流程图、文档整合。

### 新增
- 核心操作退出条件表：init/scan/context/import-db 的异常退出和降级策略
- status 命令质量评分：基于覆盖率/新鲜度/Hash 覆盖率的 A/B/C/D 评分，C/D 时输出重新扫描建议
- SKILL.md Mermaid 架构流程图：触发→状态选择→执行→验证的完整工作流

### 变更
- SKILL.md 验证章节增加质量评分检查步骤
- 项目说明.md CLI 章节引用 SKILL.md 避免重复维护

## v0.4.1 (2026-07-07)

Agent PM 产品评审驱动的改进，评分从 4.0 提升至 4.5。

### 新增
- 上下文包质量评分：`_compute_quality_grade` 函数，基于文件覆盖率/索引新鲜度/Hash 覆盖率计算 A/B/C/D 评分
- 会话恢复异常处理：定义文件损坏、摘要过时、index 与文件不一致的检测和回退路径
- doctor 输出 schema：在 `references/schema.md` 中定义 doctor 命令的 JSON 输出结构

### 变更
- SKILL.md 自动触发条件细化：明确"已获得授权"为同一会话显式激活即授权
- SKILL.md 自动触发条件合并冗余条目
- schema.md 目录结构更新为 `branches/<分支名>/` 分支隔离布局，补充 commits/commit_files/db
- workflow.md 触发前提改为指向 SKILL.md 触发纪律章节，消除文档矛盾
- SKILL.md 脚本部分补充 doctor 命令
- 评分提升计划：从 TRAICE 框架切换到三方评估法 14 维度，目标 4.8

## v0.4.0 (2026-07-07)

TRAICE 评分提升计划全部完成，25 项改进。

### 新增
- 错误信息规范化：`format_error` 函数 + 5 个异常类（GitError、ScanError、IndexError、ContextError、SessionError）
- scan 降级策略：扫描前备份索引，失败时自动回滚
- import-db 重试机制：失败时自动重试 1 次，从 .db.bak 恢复
- 大项目分批扫描：MAX_BATCH_SIZE=1000，MAX_BATCH_BYTES=10MB
- 扫描状态持久化：`scan-progress.json` 保存/加载/清理
- 置信度 reasons schema：基于规则的 reasons，格式 `{overall, reasons[]}`
- 误用警告：`check_misuse` 函数，检测项目太小、非 git 项目、临时目录等
- 一键初始化：`quickstart.py` + CLI 命令
- impact 匹配精度提升：路径前缀匹配
- CI 自动化验证：`.github/workflows/test.yml`
- 集成测试：`tests/test_integration.py`
- 可观测性指标：文件覆盖率、索引新鲜度、Hash 覆盖率
- 状态检查命令：`doctor.py` + CLI 命令
- CLI 命令帮助：每个命令增加用法说明和参数

### 变更
- SKILL.md 精简：203 行 → 162 行，详细流程拆分到 references/workflow.md
- SKILL.md 增加正例/反例、边界条件说明、文档导航
- README.md 增加 5 分钟快速开始指南
- 项目说明.md 增加完整操作示例、常见错误 FAQ（10 个）
- context_pack.py confidence 改为 `{overall, reasons[]}` 格式
- status.py 增加健康度指标

### 验证
- 40 个测试全部通过
- TRAICE 评分提升计划 25 项改进全部完成

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
