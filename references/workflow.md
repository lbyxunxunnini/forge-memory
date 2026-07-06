# Forge Memory 工作流

## 触发前提

本 workflow 默认只能在用户显式触发 `forge-memory` 后执行。

唯一允许的被动触发：用户明确表达要"全面了解项目""全面扫描项目""完整梳理项目""全量了解项目""从零梳理这个项目"等项目全貌意图。

不要因为项目很大、目录中存在 `.project-context/`、用户要求普通总结、普通局部分析或普通开发任务，就自动进入本流程。没有显式触发且未命中允许的项目全貌意图时，按常规任务处理。

## 四状态判定

触发后，先按用户意图选择状态，优先级固定：

```text
总结会话摘要 > 读取会话记忆 > 读取项目结构化文件 > 初始化
```

### 状态 1：初始化

进入条件：

- 用户说"初始化、创建项目记忆、扫描项目、生成 .project-context、第一次使用 forge-memory"。
- 或用户只说"使用 forge-memory"，但项目中不存在 `.project-context/INDEX.md`。
- 或用户说"全面扫描项目、完整梳理项目、全量了解项目"，且项目中不存在 `.project-context/INDEX.md`。

### 状态 2：总结会话摘要

进入条件：

- 用户说"总结当前会话、保存这次会话、写入会话摘要、记录当前进展、本轮结束存一下、沉淀探索结果"。

注意：这个状态不重新扫描项目，除非用户同时明确要求刷新项目结构。

### 状态 3：读取会话记忆

进入条件：

- 用户说"恢复记忆、读取项目记忆、继续上次会话、查看历史摘要、从 forge-memory 恢复上下文"。

### 状态 4：读取项目结构化文件

进入条件：

- 用户说"只读取项目结构、只看结构化摘要、读取项目全貌、不要恢复会话、不要总结摘要"。
- 用户只说"使用 forge-memory"，项目中存在 `.project-context/INDEX.md`，且用户在选项中选择此状态。

注意：这个状态只读取 `INDEX.md`、`project-summary.md`；不运行 `session list`，不读取 `sessions/*.md`，不写摘要。

### 只说"使用 forge-memory"时

- 如果项目中不存在 `.project-context/INDEX.md`：进入状态 1 初始化。
- 如果项目中存在 `.project-context/INDEX.md`：问用户选择 `读取项目结构化文件`、`读取会话记忆`、`总结会话摘要`，还是 `重新初始化/刷新扫描`。

### 不明确时

如果无法判断状态，只问一个问题：要执行 `初始化`、`总结会话摘要`、`读取会话记忆`，还是 `读取项目结构化文件`？

## 首次使用

1. 确定项目根目录。
2. 运行 `python3 <forge-memory>/forge_memory.py init <project-root>`。
3. 告知用户 `.project-context/` 已创建，并说明需要结构化扫描才能发挥作用。
4. 除非用户只要求初始化，否则运行 `python3 <forge-memory>/forge_memory.py scan <project-root>`。
5. 读取生成的 `INDEX.md` 和 `project-summary.md`。
6. 明确声明：这些结构化文件是项目全貌入口，后续工作先依据生成的上下文，再针对具体任务定向读取源码验证。

## 返回会话

1. 读取 `.project-context/INDEX.md`。
2. 运行 `python3 <forge-memory>/forge_memory.py session list <project-root>`。
3. 展示会话标题、日期、ID 和路径。
4. 除非用户要求恢复最新摘要或提供了会话 ID，否则让用户选择要恢复的摘要。
5. 读取选中的会话摘要。
6. 按需读取 `project-summary.md`。
7. 开始任务前，用几句话说明已恢复的上下文，并明确告诉模型：这些摘要就是当前项目的结构化全貌，不需要重新全量读取项目；只有遇到摘要缺口、事实冲突或任务要求源码级验证时，才定向读取相关文件。

## 读取项目结构化文件

1. 读取 `.project-context/project-summary.md`（一个文件包含项目全貌）。
2. 不读取 `sessions/*.md`，不运行 `session list`，不写入新摘要。
3. 开始任务前，用几句话说明已读取的项目全貌，并明确告诉模型：`project-summary.md` 就是项目全貌入口，不需要重新全量读取项目。

## 当前会话摘要

当用户要求总结当前会话，或长会话收尾时：

1. 选择能准确描述本次工作的具体标题。
2. 使用当前本地日期。
3. 摘要包含这些章节：
   - 摘要
   - 决策
   - 已变更或重要文件
   - 未决问题
   - 下一步
4. 运行：

```bash
python3 <forge-memory>/forge_memory.py session add <project-root> --title "标题"
```

5. 确认 `sessions/index.md` 已包含新会话。

## 结构化扫描

扫描目标是分层项目认知，不是完整源码复制。

采集：

- README、AGENTS、CLAUDE、SKILL、架构、路线图、变更日志、计划类文件。
- 包管理、构建和运行配置。
- 源码根目录、测试、脚本和应用入口。
- 目录/模块职责。
- 能通过轻量解析识别的 import 关系。
- 类、函数、命令、组件和导出名等符号。
- 入口、CLI、调度器、执行器、模型客户端、工具注册、插件、MCP、渲染、权限和安全相关文件。
- 类型、schema、协议、manifest、config、workflow、tool、memory、permission 等跨模块 contract。
- 大文件、高导入文件、关键路径、源码模块缺测试等风险信号。
- git 分支和未提交改动。

体量控制：

- 默认 Markdown 文件用于模型阅读，保持分层摘要和导航，不复制大段源码或长文档。
- `scans/latest.json` 保存紧凑索引和扫描摘要。
- `graph/*.jsonl` 是机器可读图谱。
- `index/*.jsonl` 是机器可读的文件和模块索引，含 `content_hash`。

排除：

- `.git`、`.hg`、`.svn`
- `node_modules`、`vendor`、`.venv`、`venv`
- `dist`、`build`、`out`、`target`、`.next`、`.cache`
- 日志、压缩包、图片、视频、字体、缓存锁文件、生成的 sourcemap

## 刷新上下文

以下情况应刷新扫描：

- 大量文件移动
- 依赖或框架变化
- 新增模块
- 决策改变项目方向
- 会话摘要中出现已过时的项目事实

覆盖前检查上下文文件是否包含人工备注。默认扫描会拒绝覆盖未标记为脚本生成的 Markdown；用户确认覆盖时使用 `--force`，需要保留旧内容时同时使用 `--backup`。
