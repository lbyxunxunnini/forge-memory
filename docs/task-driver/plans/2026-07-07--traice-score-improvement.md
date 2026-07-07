# TRAICE 评分提升计划 Implementation Plan

**Spec:** docs/task-driver/specs/2026-07-07--traice-score-improvement.md
**Ledger:** docs/task-driver/ledgers/2026-07-07--traice-score-improvement.md
**Mode:** single-agent
**Quality level:** Production-grade
**Status:** Approved
**Plan version:** v1
**Predecessor:** 无（首版）

## Goal

完成 forge-memory 评分提升计划的全部 25 项改进，将 TRAICE 评分从 4.5 提升到 4.8。

## Global Constraints

- 纯 Python 标准库，零外部依赖
- 保持向后兼容，不破坏现有 CLI 接口
- 文档使用中文，代码和配置保持英文
- 每个改进项必须有可验证的验收标准
- 按阶段批量执行，P0 完成后再做 P1，P1 完成后再做 P2

## Technical Decisions

### 编程语言和非编程项目扩展
- **第一层**：基于文件扩展名进行快速分类（programming/documentation/config/data/design）
- **第二层**：按流行度扩展编程语言 — Java、Rust、C/C++、Kotlin、PHP、Ruby
- **第三层**：混合特殊处理 — skill 项目、monorepo 项目、文档项目、配置项目

### 置信度 reasons schema（1.6）
- **方案**：基于规则的 reasons
- **格式**：`{overall: "high/medium/low", reasons: ["规则1", "规则2", ...]}`
- **规则**：匹配文件比例、相关文件数量、入口文件匹配

### impact 匹配精度提升（4.2）
- **方案**：综合匹配
- **算法**：文件名匹配 + 路径前缀匹配 + 模块路径匹配
- **优先级**：精确匹配 > 路径前缀匹配 > 模块路径匹配

### 大项目分批扫描（1.4）
- **方案**：按文件大小 + 数量分批
- **参数**：MAX_BATCH_SIZE = 1000，MAX_BATCH_BYTES = 10MB
- **断点恢复**：记录已完成的批次，支持从断点继续

### 误用警告（3.4）
- **方案**：智能误用检测
- **检测场景**：项目太小、非 git 项目、重复扫描、项目过大、临时目录、敏感文件
- **输出**：友好的警告信息和建议

### 一键初始化（4.1）
- **方案**：交互式 quickstart
- **流程**：检查已有索引 → 初始化 → 扫描 → 生成上下文包 → 输出使用提示
- **特性**：支持跳过已有索引、有进度提示、有使用引导

## File Map

### P0 阶段（文档改进）
- Modify: `SKILL.md` - 增加正例/反例、精简内容、增加文档导航
- Modify: `README.md` - 增加快速开始指南
- Modify: `项目说明.md` - 增加完整操作示例、常见错误 FAQ

### P1 阶段（代码+文档混合）
- Modify: `forge_memory/scanner.py` - scan 降级策略、大项目分批扫描、扫描状态持久化
- Modify: `forge_memory/context_pack.py` - 置信度 reasons schema（基于规则的 reasons）
- Modify: `forge_memory/impact.py` - impact 匹配精度提升（综合匹配）
- Modify: `forge_memory/utils.py` - 错误信息规范化
- Modify: `forge_memory/init.py` - 误用警告（智能误用检测）
- Modify: `SKILL.md` - 自动触发判断优化、触发条件示例、边界条件说明、分层文档导航
- Modify: `项目说明.md` - 端到端工作流示例
- Create: `forge_memory/quickstart.py` - 一键初始化（交互式 quickstart）
- Create: `.github/workflows/test.yml` - CI 自动化验证
- Create: `tests/test_integration.py` - 集成测试

### P2 阶段（锦上添花）
- Modify: `forge_memory/status.py` - 可观测性指标
- Create: `forge_memory/doctor.py` - 状态检查命令
- Modify: `forge_memory/scanner.py` - 默认值优化
- Modify: `SKILL.md` - CLI 命令帮助

## Interfaces

### CLI 命令
- `python3 forge_memory.py init <project-root>` - 初始化项目记忆
- `python3 forge_memory.py scan <project-root>` - 扫描项目
- `python3 forge_memory.py status <project-root>` - 查看扫描状态
- `python3 forge_memory.py context <project-root> --task "任务描述"` - 生成上下文包
- `python3 forge_memory.py impact <project-root> <file-path>` - 文件影响分析
- `python3 forge_memory.py import-db <project-root>` - 导入索引到 SQLite
- `python3 forge_memory.py session add <project-root> --title "标题"` - 添加会话摘要
- `python3 forge_memory.py session list <project-root>` - 列出会话摘要

### 新增命令（P1/P2 阶段）
- `python3 forge_memory.py quickstart <project-root>` - 一键初始化（P1）
- `python3 forge_memory.py doctor <project-root>` - 状态检查（P2）

### 配置文件
- `.project-context/context.json` - 项目元信息
- `.project-context/scan-progress.json` - 扫描进度（P1 新增）

## Tasks

### P0 阶段任务

#### Task T-001: SKILL.md 正例/反例
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-1
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 `SKILL.md` 的"触发纪律"章节增加正例（什么情况触发）
      Run: `grep -A 10 "正例" SKILL.md`
      Expected: 找到新增的正例内容
- [ ] Step 2: 在 `SKILL.md` 的"触发纪律"章节增加反例（什么情况不触发）
      Run: `grep -A 10 "反例" SKILL.md`
      Expected: 找到新增的反例内容
- [ ] Step 3: 验证正例/反例完整性
      Run: `python3 -c "import re; content=open('SKILL.md').read(); print('正例' in content, '反例' in content)"`
      Expected: `True True`
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-002: 常见错误 FAQ
**Owner role:** Implementer
**Files:** `项目说明.md`
**Acceptance:** AC-1
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 `项目说明.md` 增加 FAQ 章节
      Run: `grep -A 5 "FAQ" 项目说明.md`
      Expected: 找到新增的 FAQ 章节
- [ ] Step 2: 列出 5-10 个常见错误和解决方案
      Run: `grep -c "Q:" 项目说明.md`
      Expected: 数量 >= 5
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-003: 完整操作示例
**Owner role:** Implementer
**Files:** `项目说明.md`
**Acceptance:** AC-1
**Review gate:** spec compliance + content quality

- [ ] Step 1: 为每个 CLI 命令增加完整示例（含输入和预期输出）
      Run: `grep -A 3 "示例" 项目说明.md | head -20`
      Expected: 找到新增的示例内容
- [ ] Step 2: 验证示例完整性
      Run: `python3 -c "import re; content=open('项目说明.md').read(); cmds=['init','scan','status','context','impact','import-db','session']; print(all(cmd in content for cmd in cmds))"`
      Expected: `True`
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-004: SKILL.md 精简
**Owner role:** Implementer
**Files:** `SKILL.md`, `references/workflow.md`
**Acceptance:** AC-1
**Review gate:** spec compliance + content quality

- [ ] Step 1: 将详细流程拆分到 `references/workflow.md`
      Run: `wc -l SKILL.md`
      Expected: 行数 <= 150
- [ ] Step 2: 保留核心触发规则和状态选择
      Run: `grep -c "触发\|状态" SKILL.md`
      Expected: 数量 >= 5
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-005: 快速开始指南
**Owner role:** Implementer
**Files:** `README.md`
**Acceptance:** AC-1
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 `README.md` 增加"5 分钟快速开始"章节
      Run: `grep -A 5 "快速开始" README.md`
      Expected: 找到新增的快速开始章节
- [ ] Step 2: 只讲最核心的 3 个命令（init、scan、context）
      Run: `grep -c "init\|scan\|context" README.md`
      Expected: 数量 >= 3
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

### P1 阶段任务

#### Task T-006: 错误信息规范化
**Owner role:** Implementer
**Files:** `forge_memory/utils.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 定义错误信息格式 `[错误类型] 一句话说明 → 建议操作`
      Run: `grep -A 5 "def format_error" forge_memory/utils.py`
      Expected: 找到新增的错误格式化函数
- [ ] Step 2: 更新所有错误输出使用新格式
      Run: `grep -r "raise\|print.*Error" forge_memory/ | head -5`
      Expected: 错误输出使用新格式
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/test_utils.py -v`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-007: scan 降级策略
**Owner role:** Implementer
**Files:** `forge_memory/scanner.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 实现 scan 中途失败时自动回滚到上一次成功状态
      Run: `grep -A 10 "def scan_with_rollback" forge_memory/scanner.py`
      Expected: 找到新增的回滚函数
- [ ] Step 2: 输出明确错误信息和恢复命令
      Run: `grep -A 5 "恢复命令" forge_memory/scanner.py`
      Expected: 找到恢复命令输出
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "scan"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-008: import-db 重试机制
**Owner role:** Implementer
**Files:** `forge_memory/sqlite_backend.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 实现 import-db 失败时自动重试 1 次
      Run: `grep -A 10 "def import_db_with_retry" forge_memory/sqlite_backend.py`
      Expected: 找到新增的重试函数
- [ ] Step 2: 从 .db.bak 恢复，超过则输出人工干预指引
      Run: `grep -A 5 "人工干预" forge_memory/sqlite_backend.py`
      Expected: 找到人工干预指引输出
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "sqlite"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-009: 大项目分批扫描
**Owner role:** Implementer
**Files:** `forge_memory/scanner.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 实现超过 5000 文件时自动分批
      Run: `grep -A 10 "def scan_batch" forge_memory/scanner.py`
      Expected: 找到新增的分批函数
- [ ] Step 2: 每批完成后保存进度，中断后可从断点继续
      Run: `grep -A 5 "scan-progress.json" forge_memory/scanner.py`
      Expected: 找到进度保存逻辑
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "scan"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-010: 扫描状态持久化
**Owner role:** Implementer
**Files:** `forge_memory/scanner.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 实现扫描过程中定期写入 `.project-context/scan-progress.json`
      Run: `grep -A 10 "def save_scan_progress" forge_memory/scanner.py`
      Expected: 找到新增的进度保存函数
- [ ] Step 2: 记录已完成的文件数和批次
      Run: `grep -A 5 "completed_files\|batch" forge_memory/scanner.py`
      Expected: 找到进度记录逻辑
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "scan"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-011: 置信度 reasons schema
**Owner role:** Implementer
**Files:** `forge_memory/context_pack.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 将 confidence 从纯字符串改为 `{overall, reasons[]}`
      Run: `grep -A 10 "def generate_context_pack" forge_memory/context_pack.py | grep -A 5 "confidence"`
      Expected: 找到新的 confidence 结构
- [ ] Step 2: 说明为什么是 high/medium/low
      Run: `grep -A 5 "reasons" forge_memory/context_pack.py`
      Expected: 找到 reasons 输出
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/test_context_pack.py -v`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-012: 自动触发判断优化
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-2
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 SKILL.md 增加自动触发的判断流程图
      Run: `grep -A 10 "自动触发判断" SKILL.md`
      Expected: 找到新增的判断流程图
- [ ] Step 2: 明确什么情况下应该自动触发
      Run: `grep -A 5 "自动触发条件" SKILL.md`
      Expected: 找到明确的触发条件
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-013: 触发条件示例
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-2
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 SKILL.md 增加触发条件的正例和反例
      Run: `grep -A 10 "触发条件示例" SKILL.md`
      Expected: 找到新增的示例内容
- [ ] Step 2: 每个类别至少 2 个
      Run: `grep -c "正例\|反例" SKILL.md`
      Expected: 数量 >= 4
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-014: 边界条件说明
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-2
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 SKILL.md 明确空项目、大项目、非 git 项目等场景的行为
      Run: `grep -A 10 "边界条件" SKILL.md`
      Expected: 找到新增的边界条件说明
- [ ] Step 2: 覆盖 detached HEAD、分支名含特殊字符等场景
      Run: `grep -A 5 "detached HEAD\|特殊字符" SKILL.md`
      Expected: 找到相关说明
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-015: 误用警告
**Owner role:** Implementer
**Files:** `forge_memory/init.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 在初始化时检测常见误用场景（如项目太小、非 git 项目）
      Run: `grep -A 10 "def check_misuse" forge_memory/init.py`
      Expected: 找到新增的误用检测函数
- [ ] Step 2: 给出友好提示
      Run: `grep -A 5 "友好提示" forge_memory/init.py`
      Expected: 找到提示输出
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "init"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-016: 端到端工作流示例
**Owner role:** Implementer
**Files:** `项目说明.md`
**Acceptance:** AC-2
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在项目说明.md 增加完整的端到端示例
      Run: `grep -A 20 "端到端示例" 项目说明.md`
      Expected: 找到新增的端到端示例
- [ ] Step 2: 从初始化到生成上下文包，展示每一步的输出
      Run: `grep -A 5 "init\|scan\|context" 项目说明.md | head -20`
      Expected: 找到每一步的输出示例
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-017: 分层文档导航
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-2
**Review gate:** spec compliance + content quality

- [ ] Step 1: 在 SKILL.md 顶部增加文档导航
      Run: `head -20 SKILL.md | grep -A 5 "导航\|快速上手\|深入理解"`
      Expected: 找到新增的文档导航
- [ ] Step 2: 告诉用户"想快速上手看这里，想深入理解看那里"
      Run: `grep -A 3 "快速上手\|深入理解" SKILL.md`
      Expected: 找到导航说明
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-018: 一键初始化
**Owner role:** Implementer
**Files:** `forge_memory/quickstart.py`, `forge_memory.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 创建 `forge_memory/quickstart.py` 实现一键初始化
      Run: `ls -la forge_memory/quickstart.py`
      Expected: 文件存在
- [ ] Step 2: 自动执行 init + scan + 生成示例上下文包
      Run: `grep -A 10 "def quickstart" forge_memory/quickstart.py`
      Expected: 找到 quickstart 函数
- [ ] Step 3: 在 `forge_memory.py` 中添加 quickstart 命令
      Run: `grep -A 5 "quickstart" forge_memory.py`
      Expected: 找到 quickstart 命令处理
- [ ] Step 4: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "quickstart"`
      Expected: 测试通过
- [ ] Step 5: 写 TaskResult packet 到 ledger
- [ ] Step 6: 写 ReviewReport packet 到 ledger

#### Task T-019: impact 匹配精度提升
**Owner role:** Implementer
**Files:** `forge_memory/impact.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 对同名不同模块的文件增加路径前缀匹配
      Run: `grep -A 10 "def match_file" forge_memory/impact.py`
      Expected: 找到路径前缀匹配逻辑
- [ ] Step 2: 减少误匹配
      Run: `grep -A 5 "前缀匹配" forge_memory/impact.py`
      Expected: 找到匹配精度提升逻辑
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/test_impact.py -v`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-020: CI 自动化验证
**Owner role:** Implementer
**Files:** `.github/workflows/test.yml`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 创建 `.github/workflows/test.yml`
      Run: `ls -la .github/workflows/test.yml`
      Expected: 文件存在
- [ ] Step 2: push 时自动运行 `python3 -m unittest discover`
      Run: `grep -A 5 "unittest discover" .github/workflows/test.yml`
      Expected: 找到测试运行配置
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-021: 集成测试
**Owner role:** Implementer
**Files:** `tests/test_integration.py`
**Acceptance:** AC-2
**Review gate:** spec compliance + code quality

- [ ] Step 1: 创建 `tests/test_integration.py`
      Run: `ls -la tests/test_integration.py`
      Expected: 文件存在
- [ ] Step 2: 添加端到端测试：init→scan→status→context→impact→import-db
      Run: `grep -A 20 "def test_full_workflow" tests/test_integration.py`
      Expected: 找到端到端测试
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/test_integration.py -v`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

### P2 阶段任务

#### Task T-022: 可观测性指标
**Owner role:** Implementer
**Files:** `forge_memory/status.py`
**Acceptance:** AC-3
**Review gate:** spec compliance + code quality

- [ ] Step 1: status 命令输出索引健康度
      Run: `grep -A 10 "def get_status" forge_memory/status.py | grep -A 5 "health"`
      Expected: 找到健康度输出
- [ ] Step 2: files.jsonl 行数 vs 项目实际文件数
      Run: `grep -A 5 "file_count" forge_memory/status.py`
      Expected: 找到文件数对比
- [ ] Step 3: commits.jsonl 最新时间 vs 当前时间差
      Run: `grep -A 5 "last_commit_time" forge_memory/status.py`
      Expected: 找到时间差输出
- [ ] Step 4: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "status"`
      Expected: 测试通过
- [ ] Step 5: 写 TaskResult packet 到 ledger
- [ ] Step 6: 写 ReviewReport packet 到 ledger

#### Task T-023: CLI 命令帮助
**Owner role:** Implementer
**Files:** `SKILL.md`
**Acceptance:** AC-3
**Review gate:** spec compliance + content quality

- [ ] Step 1: 每个命令支持 `--help` 参数
      Run: `grep -A 5 "\-\-help" SKILL.md`
      Expected: 找到 --help 说明
- [ ] Step 2: 输出用法说明和示例
      Run: `grep -A 3 "用法\|示例" SKILL.md | head -20`
      Expected: 找到用法和示例
- [ ] Step 3: 写 TaskResult packet 到 ledger
- [ ] Step 4: 写 ReviewReport packet 到 ledger

#### Task T-024: 默认值优化
**Owner role:** Implementer
**Files:** `forge_memory/scanner.py`
**Acceptance:** AC-3
**Review gate:** spec compliance + code quality

- [ ] Step 1: scan 命令自动检测项目类型
      Run: `grep -A 10 "def detect_project_type" forge_memory/scanner.py`
      Expected: 找到项目类型检测函数
- [ ] Step 2: 设置合理的默认参数
      Run: `grep -A 5 "default_params" forge_memory/scanner.py`
      Expected: 找到默认参数设置
- [ ] Step 3: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "scan"`
      Expected: 测试通过
- [ ] Step 4: 写 TaskResult packet 到 ledger
- [ ] Step 5: 写 ReviewReport packet 到 ledger

#### Task T-025: 状态检查命令
**Owner role:** Implementer
**Files:** `forge_memory/doctor.py`, `forge_memory.py`
**Acceptance:** AC-3
**Review gate:** spec compliance + code quality

- [ ] Step 1: 创建 `forge_memory/doctor.py` 实现状态检查
      Run: `ls -la forge_memory/doctor.py`
      Expected: 文件存在
- [ ] Step 2: 检查环境依赖和索引健康状态
      Run: `grep -A 10 "def doctor" forge_memory/doctor.py`
      Expected: 找到 doctor 函数
- [ ] Step 3: 在 `forge_memory.py` 中添加 doctor 命令
      Run: `grep -A 5 "doctor" forge_memory.py`
      Expected: 找到 doctor 命令处理
- [ ] Step 4: 运行测试验证
      Run: `python3 -m pytest tests/ -v -k "doctor"`
      Expected: 测试通过
- [ ] Step 5: 写 TaskResult packet 到 ledger
- [ ] Step 6: 写 ReviewReport packet 到 ledger

## Verification Plan

### P0 阶段验证
- Run: `grep -c "正例\|反例" SKILL.md`
  Expected: 数量 >= 4
  Covers: AC-1
  Evidence strength: strong

- Run: `grep -c "Q:" 项目说明.md`
  Expected: 数量 >= 5
  Covers: AC-1
  Evidence strength: strong

- Run: `wc -l SKILL.md`
  Expected: 行数 <= 150
  Covers: AC-1
  Evidence strength: strong

- Run: `grep -c "快速开始" README.md`
  Expected: 数量 >= 1
  Covers: AC-1
  Evidence strength: strong

### P1 阶段验证
- Run: `python3 -m pytest tests/ -v`
  Expected: 所有测试通过
  Covers: AC-2, AC-6
  Evidence strength: strong

- Run: `python3 forge_memory.py quickstart /tmp/test-project`
  Expected: 成功初始化并生成上下文包
  Covers: AC-2
  Evidence strength: strong

- Run: `python3 -m pytest tests/test_integration.py -v`
  Expected: 端到端测试通过
  Covers: AC-2
  Evidence strength: strong

### P2 阶段验证
- Run: `python3 forge_memory.py doctor /tmp/test-project`
  Expected: 输出环境依赖和索引健康状态
  Covers: AC-3
  Evidence strength: strong

- Run: `python3 forge_memory.py status /tmp/test-project`
  Expected: 输出索引健康度指标
  Covers: AC-3
  Evidence strength: strong

### 最终验证
- Run: `python3 -m pytest tests/ -v`
  Expected: 所有测试通过
  Covers: AC-4, AC-5, AC-6
  Evidence strength: strong

## Stop Conditions

- 任何测试失败且无法在 2 轮内修复
- 任何改进项影响现有功能且无法回滚
- 用户要求暂停或终止

## PlanPacket

```yaml
plan_path: docs/task-driver/plans/2026-07-07--traice-score-improvement.md
ledger_path: docs/task-driver/ledgers/2026-07-07--traice-score-improvement.md
plan_version: v1
predecessor: 无
mode: single-agent
tasks:
  - id: T-001
    owner_role: Implementer
    objective: SKILL.md 正例/反例
    files: [SKILL.md]
    verification: grep -c "正例\|反例" SKILL.md
    acceptance_ac_ids: [AC-1]
  - id: T-002
    owner_role: Implementer
    objective: 常见错误 FAQ
    files: [项目说明.md]
    verification: grep -c "Q:" 项目说明.md
    acceptance_ac_ids: [AC-1]
  - id: T-003
    owner_role: Implementer
    objective: 完整操作示例
    files: [项目说明.md]
    verification: grep -c "示例" 项目说明.md
    acceptance_ac_ids: [AC-1]
  - id: T-004
    owner_role: Implementer
    objective: SKILL.md 精简
    files: [SKILL.md, references/workflow.md]
    verification: wc -l SKILL.md
    acceptance_ac_ids: [AC-1]
  - id: T-005
    owner_role: Implementer
    objective: 快速开始指南
    files: [README.md]
    verification: grep -c "快速开始" README.md
    acceptance_ac_ids: [AC-1]
  - id: T-006
    owner_role: Implementer
    objective: 错误信息规范化
    files: [forge_memory/utils.py]
    verification: python3 -m pytest tests/test_utils.py -v
    acceptance_ac_ids: [AC-2]
  - id: T-007
    owner_role: Implementer
    objective: scan 降级策略
    files: [forge_memory/scanner.py]
    verification: python3 -m pytest tests/ -v -k "scan"
    acceptance_ac_ids: [AC-2]
  - id: T-008
    owner_role: Implementer
    objective: import-db 重试机制
    files: [forge_memory/sqlite_backend.py]
    verification: python3 -m pytest tests/ -v -k "sqlite"
    acceptance_ac_ids: [AC-2]
  - id: T-009
    owner_role: Implementer
    objective: 大项目分批扫描
    files: [forge_memory/scanner.py]
    verification: python3 -m pytest tests/ -v -k "scan"
    acceptance_ac_ids: [AC-2]
  - id: T-010
    owner_role: Implementer
    objective: 扫描状态持久化
    files: [forge_memory/scanner.py]
    verification: python3 -m pytest tests/ -v -k "scan"
    acceptance_ac_ids: [AC-2]
  - id: T-011
    owner_role: Implementer
    objective: 置信度 reasons schema
    files: [forge_memory/context_pack.py]
    verification: python3 -m pytest tests/test_context_pack.py -v
    acceptance_ac_ids: [AC-2]
  - id: T-012
    owner_role: Implementer
    objective: 自动触发判断优化
    files: [SKILL.md]
    verification: grep -c "自动触发判断" SKILL.md
    acceptance_ac_ids: [AC-2]
  - id: T-013
    owner_role: Implementer
    objective: 触发条件示例
    files: [SKILL.md]
    verification: grep -c "触发条件示例" SKILL.md
    acceptance_ac_ids: [AC-2]
  - id: T-014
    owner_role: Implementer
    objective: 边界条件说明
    files: [SKILL.md]
    verification: grep -c "边界条件" SKILL.md
    acceptance_ac_ids: [AC-2]
  - id: T-015
    owner_role: Implementer
    objective: 误用警告
    files: [forge_memory/init.py]
    verification: python3 -m pytest tests/ -v -k "init"
    acceptance_ac_ids: [AC-2]
  - id: T-016
    owner_role: Implementer
    objective: 端到端工作流示例
    files: [项目说明.md]
    verification: grep -c "端到端示例" 项目说明.md
    acceptance_ac_ids: [AC-2]
  - id: T-017
    owner_role: Implementer
    objective: 分层文档导航
    files: [SKILL.md]
    verification: grep -c "导航" SKILL.md
    acceptance_ac_ids: [AC-2]
  - id: T-018
    owner_role: Implementer
    objective: 一键初始化
    files: [forge_memory/quickstart.py, forge_memory.py]
    verification: python3 -m pytest tests/ -v -k "quickstart"
    acceptance_ac_ids: [AC-2]
  - id: T-019
    owner_role: Implementer
    objective: impact 匹配精度提升
    files: [forge_memory/impact.py]
    verification: python3 -m pytest tests/test_impact.py -v
    acceptance_ac_ids: [AC-2]
  - id: T-020
    owner_role: Implementer
    objective: CI 自动化验证
    files: [.github/workflows/test.yml]
    verification: cat .github/workflows/test.yml
    acceptance_ac_ids: [AC-2]
  - id: T-021
    owner_role: Implementer
    objective: 集成测试
    files: [tests/test_integration.py]
    verification: python3 -m pytest tests/test_integration.py -v
    acceptance_ac_ids: [AC-2]
  - id: T-022
    owner_role: Implementer
    objective: 可观测性指标
    files: [forge_memory/status.py]
    verification: python3 -m pytest tests/ -v -k "status"
    acceptance_ac_ids: [AC-3]
  - id: T-023
    owner_role: Implementer
    objective: CLI 命令帮助
    files: [SKILL.md]
    verification: grep -c "\-\-help" SKILL.md
    acceptance_ac_ids: [AC-3]
  - id: T-024
    owner_role: Implementer
    objective: 默认值优化
    files: [forge_memory/scanner.py]
    verification: python3 -m pytest tests/ -v -k "scan"
    acceptance_ac_ids: [AC-3]
  - id: T-025
    owner_role: Implementer
    objective: 状态检查命令
    files: [forge_memory/doctor.py, forge_memory.py]
    verification: python3 -m pytest tests/ -v -k "doctor"
    acceptance_ac_ids: [AC-3]
stop_conditions:
  - 任何测试失败且无法在 2 轮内修复
  - 任何改进项影响现有功能且无法回滚
  - 用户要求暂停或终止
status: approved
```
