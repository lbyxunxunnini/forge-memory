# Forge Memory — 项目规则

## 项目信息

- **名称**：forge-memory
- **版本**：v0.4.7
- **定位**：项目记忆层，负责项目认知和上下文供给
- **GitHub**：[lbyxunxunnini/forge-memory](https://github.com/lbyxunxunnini/forge-memory)
- **父级规则**：[agent设计/CLAUDE.md](../CLAUDE.md)

## 关键文件

| 文件 | 职责 |
|------|------|
| `SKILL.md` | 触发规则、四状态选择器、脚本命令 |
| `references/workflow.md` | 详细工作流（首次使用、恢复记忆、会话摘要、扫描） |
| `references/schema.md` | `.project-context/` 目录结构和 JSONL schema |
| `forge_memory.py` | CLI 统一入口 |
| `forge_memory/` | Python 模块（scanner、indexer、grapher、session 等） |
| `tests/` | 单元测试和集成测试 |
| `VERSION` | 当前版本号 |
| `CHANGELOG.md` | 版本日志 |

## 开发规则

- Python 脚本只使用标准库（零依赖）
- 所有脚本必须可独立运行，不依赖隐含的全局状态
- `.project-context/` 使用分支隔离存储：`branches/<分支名>/`
- schema.md 是编辑 `.project-context/` 文件前的必读参考
- 测试用 `python3 -m unittest discover tests/` 运行
- 输出面向用户的文档使用中文，代码和配置保持英文

## 版本管理

- 5 处版本号同步：`SKILL.md` / `VERSION` / `.skillhub.json` / `README.md` / `CHANGELOG.md`
- 版本对齐基准：本地 `VERSION` 文件
- 发布前运行 `bash scripts/release_checks/metadata.sh`
- 详细发布流程见 [docs/skill-publishing.md](../docs/skill-publishing.md)

## Git 约束

- 提交信息前缀：`feat:` / `fix:` / `docs:` / `refactor:`
- 独立推送到 GitHub，不与其他子项目共享 git 历史
