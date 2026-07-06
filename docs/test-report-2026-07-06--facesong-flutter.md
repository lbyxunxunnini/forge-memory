# Forge Memory v0.1 测试报告

**测试日期：** 2026-07-06
**测试项目：** facesong_flutter（Flutter/Dart 音乐播放器项目）
**项目路径：** `/Users/agi00114/Desktop/flutter项目/facesong_flutter`
**Forge Memory 版本：** v0.1.0

## 测试环境

- macOS Darwin 24.6.0
- Python 3（标准库，零依赖）
- 项目规模：3006 个文件，31 个模块

## 测试结果总览

| 测试项 | 结果 | 说明 |
|---|---|---|
| init | **通过** | 创建完整 .project-context/ 目录结构 |
| scan（首次） | **通过** | 3006 文件、31 模块、6222 节点、13757 关系 |
| scan（增量） | **通过** | 3006 unchanged, 0 changed, 0 new, 0 deleted |
| status | **通过** | 正确显示项目名、扫描时间、文件数、模块数 |
| context（中文关键词） | **通过** | 置信度 low，正确输出 caveat |
| context（英文关键词） | **通过** | 正确匹配 player 相关文件（15 个） |
| context（带入口文件） | **通过** | 入口文件 lib/app.dart 正确排在首位 |
| session list | **通过** | 正确返回空列表（无历史会话） |
| 输出文件完整性 | **通过** | 12 个输出文件全部存在且非空 |
| content_hash 正确性 | **通过** | 3006 条记录全部含 sha256 hash |
| 排除规则 | **通过** | node_modules、.git、build 等排除目录未被索引 |
| project-summary.md | **通过** | 27238 bytes，含项目概览、运行链路、风险地图等 |

## 详细测试记录

### 1. 初始化

```bash
python3 forge_memory.py init /Users/agi00114/Desktop/flutter项目/facesong_flutter --allow-empty-root
```

**结果：** 成功创建 6 个文件/目录：
- `.project-context/`
- `.project-context/sessions/`
- `.project-context/context.json`（302 bytes）
- `.project-context/INDEX.md`（957 bytes）
- `.project-context/project-summary.md`（占位）
- `.project-context/sessions/index.md`

### 2. 首次扫描

```bash
python3 forge_memory.py scan /Users/agi00114/Desktop/flutter项目/facesong_flutter
```

**结果：**
- 已索引文件：3006
- 已索引模块：31
- 图谱节点：6222
- 图谱关系：13757
- 变更文件：0，未变：0，新增：3006，删除：0

**输出文件大小：**
| 文件 | 大小 |
|---|---|
| index/files.jsonl | 1,473,647 bytes |
| index/modules.jsonl | 6,148 bytes |
| graph/nodes.jsonl | 1,654,302 bytes |
| graph/edges.jsonl | 2,356,314 bytes |
| project-summary.md | 27,238 bytes |
| graph/mermaid.md | 11,829 bytes |

### 3. 增量扫描

```bash
python3 forge_memory.py scan /Users/agi00114/Desktop/flutter项目/facesong_flutter
```

**结果：** `changed=0, unchanged=3006, new=0, deleted=0`

增量扫描正确识别所有文件未变化，跳过重新计算 content_hash。

### 4. 状态查询

```bash
python3 forge_memory.py status /Users/agi00114/Desktop/flutter项目/facesong_flutter
```

**输出：**
```
项目：facesong_flutter
状态：success
最后扫描：2026-07-06T11:38:54+08:00
文件总数：3006
模块总数：31
```

### 5. 上下文包生成（中文关键词）

```bash
python3 forge_memory.py context --task "修复歌曲播放卡顿"
```

**结果：**
- 置信度：**low**
- 匹配关键词：修复, 歌曲, 播放, 卡顿
- 相关文件数：0
- 正确输出 caveat 警告
- 风险点识别到大文件（`invite_copy_link.json` 269KB、`create_master.dart` 83KB）
- 高导入文件识别到 `lib/app.dart`（28 个 import）

**评估：** 中文关键词未做分词，导致匹配率为零。这是已知限制，caveat 正确提示用户。

### 6. 上下文包生成（英文关键词）

```bash
python3 forge_memory.py context --task "修改播放器 player 模块"
```

**结果：**
- 正确匹配到 15 个 player 相关文件
- 包括：`floating_player.dart`、`player_controller.dart`、`player.dart`、`player_control_area.dart`、`suspension_player.dart` 等
- 入口文件识别准确

### 7. 上下文包生成（带入口文件）

```bash
python3 forge_memory.py context --task "修改播放器播放逻辑" --entry "lib/app.dart"
```

**结果：**
- 入口文件 `lib/app.dart` 正确排在 Likely Entry Files 首位
- 高导入文件列表正确包含 `lib/app.dart`（28 个 import）

### 8. content_hash 验证

- 3006 条文件记录全部包含 `content_hash` 字段
- hash 长度为 64 字符（sha256 hex）
- 无缺失记录

### 9. 排除规则验证

扫描结果中不包含以下目录的文件：
- `.git/`
- `node_modules/`
- `build/`
- `.dart_tool/`（项目中存在但被排除）

### 10. project-summary.md 内容验证

27,238 bytes 的合并摘要，包含：
- 项目概览（清单、用途、技术信号、文档信号）
- 运行链路
- 核心 Contract
- 风险地图（大文件、无测试模块）
- Worktree 快照
- Skill/Agent 专项摘要
- Mermaid 图谱

## 已知限制

| 限制 | 影响 | 缓解方案 |
|---|---|---|
| 中文关键词匹配率低 | context 包对中文任务描述置信度为 low | 输出 caveat 提示用户；后续版本可加中文分词 |
| 无 Git 历史分析 | context 包不含近期变更信息 | v0.3 将加入 |
| 无测试文件 | 项目中未发现 `_test.dart` 文件 | 建议测试识别为"未找到建议的测试文件" |
| `.trae/` 目录被扫描 | 包含 IDE 插件文件，增加噪音 | 后续可将 `.trae` 加入 EXCLUDE_DIRS |
| 大项目首次扫描耗时 | 3006 文件扫描约 10 秒 | 后续版本可加并发 |

## 结论

Forge Memory v0.1 在 facesong_flutter（3006 文件的 Flutter 项目）上**全部测试通过**：

- 首次扫描和增量扫描均正常
- 所有 12 个输出文件完整且格式正确
- content_hash 全覆盖
- 上下文包对英文关键词匹配准确，对中文关键词正确输出 caveat
- 排除规则有效
- project-summary.md 内容充实

**状态：可交付**
