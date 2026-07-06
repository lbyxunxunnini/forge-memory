---
slug: forge-memory-user-88546431
displayName: Forge Memory
version: 0.3.1
summary: 项目记忆层，负责项目认知和上下文供给，支持分支隔离、Git 历史、影响分析和 SQLite 索引。
tags: [memory, project, context, workflow, index]
license: MIT
name: forge-memory
description: 项目记忆层，负责项目认知和上下文供给。当智能体需要理解项目全貌、生成任务上下文包、分析文件影响、恢复历史会话、扫描项目索引、或任务驱动框架计划阶段需要项目上下文时触发。支持分支隔离存储、Git 历史、SQLite 索引。初始化、扫描、状态查询、上下文生成、影响分析、会话记忆均由此 skill 管理。
---

# Forge Memory

## 目标

在用户显式触发，或用户明确要求全面了解/全面扫描项目时，使用本 skill 在项目根目录创建或读取 `.project-context/`，作为项目本地记忆层。
它让 Claude Code 面对大型项目时先读取结构化摘要和知识图谱，再按需定向读取源码。

这个 skill 负责项目认知，不负责源码备份。摘要和图谱应描述结构、决策、关系、风险和会话状态，不应大段复制源码。

## 读取参考

执行前按需读取：

- `references/workflow.md`：首次使用、恢复记忆、会话摘要、结构化扫描流程。
- `references/schema.md`：编辑 `.project-context/` 文件或 graph JSONL 前必须读取。

## 触发纪律

本 skill 支持自动触发和手动触发。

自动触发条件（智能体按需调用）：

- 任务驱动框架计划阶段需要项目上下文。
- 智能体需要全面了解项目结构和历史。
- 项目已有 `.project-context/` 且智能体需要恢复上下文。
- 其他 skill 需要项目上下文且已获得授权。

手动触发条件：

- 用户显式写 `$forge-memory`。
- 用户明确说"使用 forge-memory"或"调用项目记忆"。
- 用户明确要求初始化、扫描、恢复或写入 `.project-context/`。
- 用户明确要求运行本 skill 的脚本。
- 用户明确说"需要全面了解项目""全面扫描项目""完整梳理项目""全量了解项目""从零梳理这个项目"等项目全貌意图。

以下情况不触发：

- 只是遇到大型项目但不需要上下文。
- 用户只是要求普通代码修改、文档编写、局部项目分析或会话总结。
- 用户只是说"看一下这个文件/模块""帮我修 bug""解释这段代码"等局部任务。

## 四状态选择器

确认命中自动触发或手动触发条件后，按以下优先级判断状态：

`总结会话摘要` > `读取会话记忆` > `读取项目结构化文件` > `初始化`

详细判定逻辑见 `references/workflow.md` 的"四状态判定"章节。

**四种状态**：
1. **初始化**：创建 `.project-context/` 并运行结构化扫描
2. **总结会话摘要**：将当前会话写入 `sessions/`，不重新扫描项目
3. **读取会话记忆**：读取历史会话摘要恢复上下文
4. **读取项目结构化文件**：只读取 `project-summary.md`（一个文件包含项目全貌）

### 状态 1：初始化

进入条件：

- 用户明确要求初始化/扫描/创建项目记忆。
- 或用户只说使用 forge-memory，且目标项目没有 `.project-context/INDEX.md`。

执行：

   - 运行 `python3 <forge-memory>/forge_memory.py init <project-root>`。
   - 告知用户已创建上下文目录，接下来需要结构化扫描。
   - 除非用户只要求初始化，否则运行 `python3 <forge-memory>/forge_memory.py scan <project-root>`。

### 状态 2：总结会话摘要

进入条件：

- 用户明确要求总结当前会话、保存这次会话、写入会话摘要、记录当前进展、本轮结束存一下、沉淀探索结果。

执行：

   - 不重新扫描项目，除非用户同时明确要求刷新项目结构。
   - 生成具体标题，并使用当前日期。
   - 通过 stdin 或 `--from-file` 运行 `python3 <forge-memory>/forge_memory.py session add <project-root> --title "<标题>"`。
   - 摘要必须包含：摘要、决策、已变更或重要文件、未决问题、下一步。

### 状态 3：读取会话记忆

进入条件：

- 用户明确要求读取/恢复/继续历史记忆。
- 或用户只说使用 forge-memory，且目标项目已有 `.project-context/INDEX.md`。

执行：

   - 读取 `.project-context/INDEX.md`。
   - 读取 `.project-context/project-summary.md`。
   - 运行 `python3 <forge-memory>/forge_memory.py session list <project-root>` 或查看 `sessions/index.md`。
   - 列出可用会话摘要，让用户选择要恢复的摘要；如果用户指定了会话 ID 或要求恢复最新摘要，则直接读取。
   - 读取选中的会话摘要，以及其中关联的项目摘要文件。
   - 明确告诉后续模型：这些结构化文件是项目全貌入口和已沉淀上下文，不需要重新全量读取项目；只有摘要标出缺口或当前任务需要源码事实验证时，才定向读取相关文件。

### 状态 4：读取项目结构化文件

进入条件：

- 用户明确要求只读取项目结构化摘要、只看项目全貌、不要恢复会话、不要总结摘要。
- 或用户只说使用 forge-memory，项目已有 `.project-context/INDEX.md`，且用户在选项中选择此状态。

执行：

   - 读取 `.project-context/project-summary.md`（一个文件包含项目全貌）。
   - 不运行 `session list`，不读取 `sessions/*.md`，不写入新的会话摘要。
   - 明确告诉后续模型：`project-summary.md` 就是项目全貌入口，不需要重新全量读取项目；只有摘要缺口、事实冲突或任务要求源码级验证时，才定向读取相关文件。

## 必须遵守

- 返回会话时优先读取 `.project-context/`，不要直接进行大范围项目读取。
- 读取会话摘要和结构化项目文本后，必须把它们当作"项目全貌入口"传达给后续模型，避免模型误以为仍需从零读完整项目。
- 用户选择"读取项目结构化文件"时，不得自动读取或恢复会话摘要。
- 默认只读取 `project-summary.md` 即可获得项目全貌，无需读取其他文件。
- 扫描时排除构建产物、依赖缓存、VCS 元数据、虚拟环境、日志和二进制文件。
- 如果上下文文件与当前源码事实冲突，先用源码验证，再记录冲突并更新相关上下文。
- 遇到非脚本生成的用户手写摘要，不要擅自覆盖，先询问。

## 脚本

所有脚本使用 Python 标准库，通过 `forge_memory.py` 统一入口调用。

```bash
python3 <forge-memory>/forge_memory.py init <project-root>
python3 <forge-memory>/forge_memory.py scan <project-root>
python3 <forge-memory>/forge_memory.py scan <project-root> --force --backup
python3 <forge-memory>/forge_memory.py status <project-root>
python3 <forge-memory>/forge_memory.py context <project-root> --task "任务描述"
python3 <forge-memory>/forge_memory.py context <project-root> --task "任务描述" --entry "path/to/file"
python3 <forge-memory>/forge_memory.py impact <project-root> <file-path>
python3 <forge-memory>/forge_memory.py import-db <project-root>
python3 <forge-memory>/forge_memory.py session add <project-root> --title "会话标题"
python3 <forge-memory>/forge_memory.py session add <project-root> --title "会话标题" --from-file summary.md
python3 <forge-memory>/forge_memory.py session list <project-root>
python3 <forge-memory>/forge_memory.py session list <project-root> --json
```

## 验证

创建或更新项目记忆后：

1. 确认 `.project-context/INDEX.md` 存在。
2. 确认 `.project-context/project-summary.md` 存在且内容充实。
3. 确认新的会话摘要出现在 `sessions/index.md`，并且可以被列出。
4. 至少抽查一条摘要中的源码事实，确认与源码一致。

### 质量评估

扫描完成后，检查以下质量指标：

- **文件覆盖率**：已索引文件数 / 项目实际文件数（排除排除目录）
- **摘要充实度**：`project-summary.md` 是否包含项目用途、技术栈、主要模块等关键信息

如发现覆盖率过低或摘要过于单薄，提示用户可能需要调整 `--max-file-bytes` 参数或手动补充关键文件的摘要。

## 需要暂停询问

以下情况必须暂停并询问用户：

- 目标项目根目录不明确。
- `.project-context/` 已存在，且将要覆盖用户手写内容。
- 用户要求持久自动化、后台监听、数据库或外部服务。
- 扫描发现敏感文件，不确定是否可以总结。
- 项目过大，单次扫描无法形成有效摘要，需要先确认范围。

## 设计决策

**为什么采用单次扫描而非迭代循环**：本 skill 定位为轻量级项目结构化工具，核心价值是快速生成项目全貌摘要。扫描过程是确定性的（基于文件系统遍历和规则提取），不存在"做得好不好"的评估空间——只要文件存在且可读，就能生成摘要。迭代循环适用于需要主观评估的场景（如 UI 设计、文案生成），不适用于本工具类 skill。

如需增强扫描质量，应通过调整脚本参数（如 `--max-file-bytes`）或手动补充摘要实现，而非引入迭代机制。
