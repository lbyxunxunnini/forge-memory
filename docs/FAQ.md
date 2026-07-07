# 常见问题 FAQ

## 使用问题

### Q1: 运行 init 命令时报错 "已存在 .project-context 目录"
**原因**：项目已经初始化过，重复初始化会覆盖现有数据。
**解决**：
- 如果想重新初始化，使用 `--force` 参数：`python3 forge_memory.py init <项目目录> --force`
- 如果想保留现有数据，直接使用 `scan` 命令更新索引

### Q2: 运行 scan 命令时超时或中断
**原因**：项目文件过多，单次扫描耗时过长。
**解决**：
- 使用 `--max-files` 参数限制扫描文件数：`python3 forge_memory.py scan <项目目录> --max-files 1000`
- 使用 `--batch-size` 参数分批扫描：`python3 forge_memory.py scan <项目目录> --batch-size 500`
- 扫描过程中会显示进度（每 200 个文件），中断后可直接重新运行，支持增量扫描

### Q3: 生成的上下文包不准确
**原因**：任务描述与项目索引的匹配度不足。
**解决**：
- 使用更具体的任务描述，包含关键词
- 使用 `--entry` 参数指定入口文件：`python3 forge_memory.py context <项目目录> --task "任务" --entry "path/to/file"`
- 先运行 `scan` 更新索引

### Q4: impact 命令找不到相关文件
**原因**：文件路径不正确或索引未更新。
**解决**：
- 检查文件路径是否正确（相对于项目根目录）
- 运行 `scan` 更新索引
- 使用 `status` 命令检查索引状态

### Q5: import-db 命令失败
**原因**：SQLite 数据库损坏或文件权限问题。
**解决**：
- 检查 `.project-context/branches/<分支名>/forge-memory.db` 文件是否存在
- 使用 `--backup` 参数从备份恢复：`python3 forge_memory.py import-db <项目目录> --backup`
- 删除数据库文件重新导入

### Q6: 非 git 项目无法使用
**原因**：forge-memory 依赖 git 进行分支检测和 commit 历史记录。
**解决**：
- 先初始化 git：`git init`
- 或使用 `--no-git` 参数（部分功能受限）：`python3 forge_memory.py scan <项目目录> --no-git`

### Q7: 项目太小（< 10 个文件）时扫描无意义
**原因**：小项目不需要复杂的索引和上下文包。
**解决**：
- 直接阅读项目文件，不需要使用 forge-memory
- 或使用 `--force` 参数强制扫描

### Q8: 扫描时包含敏感文件（.env、credentials）
**原因**：默认扫描会包含所有文件，可能泄露敏感信息。
**解决**：
- 使用 `.gitignore` 排除敏感文件
- 或使用 `--exclude` 参数手动排除：`python3 forge_memory.py scan <项目目录> --exclude ".env" "credentials*"`

### Q9: 会话摘要无法恢复
**原因**：会话文件损坏或路径不正确。
**解决**：
- 检查 `sessions/index.md` 文件是否存在
- 使用 `session list` 命令查看可用会话：`python3 forge_memory.py session list <项目目录>`
- 手动恢复：直接阅读 `sessions/*.md` 文件

### Q10: 大项目（> 10000 文件）扫描性能差
**原因**：单线程扫描，文件过多导致耗时过长。
**解决**：
- 使用 `--max-files` 参数限制扫描文件数
- 使用 `--batch-size` 参数分批扫描
- 使用 `--skip-tests` 参数跳过测试文件：`python3 forge_memory.py scan <项目目录> --skip-tests`

## 错误信息解读

### [ScanError] 扫描中途失败
扫描过程中遇到不可恢复的错误。工具会自动回滚到上一次成功的索引状态。
**解决**：查看错误详情，修复后重新运行 `scan`。如果回滚也失败，会提示手动恢复命令。

### [IndexError] 导入失败
JSONL 导入 SQLite 时出错。工具会自动重试（从备份恢复后重试）。
**解决**：如果多次重试仍失败，按提示的"人工干预"命令操作。

### [ContextError] 上下文包生成失败
读取索引文件或生成上下文包时出错。
**解决**：索引可能不完整，重新运行 `scan`。

### [GitError] git 命令不可用
git 不在 PATH 中或项目不是 git 仓库。
**解决**：安装 git 或运行 `git init`。部分功能会降级但不影响核心扫描。

### [FatalError] 未预期的错误
程序遇到未处理的异常。
**解决**：运行 `forge_memory.py doctor` 检查环境，或在 GitHub 报告 issue。
