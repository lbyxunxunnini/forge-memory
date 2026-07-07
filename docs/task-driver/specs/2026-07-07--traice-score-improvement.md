# TRAICE 评分提升计划 Spec

**Date:** 2026-07-07
**Quality level:** Production-grade
**Status:** Approved

## Goal

完成 forge-memory 评分提升计划的全部 25 项改进，将 TRAICE 评分从 4.5 提升到 4.8。

## User And Scenario

forge-memory 用户（智能体开发者）在使用项目记忆层时，遇到以下痛点：
- 反模式与FAQ缺失（3.5分），不知道哪些情况不该用，容易用错
- 异常处理不完善（4.3分），出错时不知道如何修复
- 运行稳定性不足（4.3分），大项目中断后需从头扫描
- 文档质量待提升（4.3分），缺少完整操作示例
- 渐进式披露不足（4.3分），首次阅读成本高

## Scope

### P0 阶段（目标 4.6 分）
- 3.1 SKILL.md 正例/反例
- 3.3 常见错误 FAQ
- 3.5 完整操作示例
- 3.8 SKILL.md 精简
- 3.9 快速开始指南

### P1 阶段（目标 4.7 分）
- 1.1 错误信息规范化
- 1.2 scan 降级策略
- 1.3 import-db 重试机制
- 1.4 大项目分批扫描
- 1.5 扫描状态持久化
- 1.6 置信度 reasons schema
- 2.1 自动触发判断优化
- 2.2 触发条件示例
- 3.2 边界条件说明
- 3.4 误用警告
- 3.6 端到端工作流示例
- 3.10 分层文档导航
- 4.1 一键初始化
- 4.2 impact 匹配精度提升
- 4.3 CI 自动化验证
- 4.4 集成测试

### P2 阶段（目标 4.8 分）
- 1.7 可观测性指标
- 3.7 CLI 命令帮助
- 4.5 默认值优化
- 4.6 状态检查命令

## Non-Goals

- 不改变 forge-memory 的核心架构和数据模型
- 不引入外部依赖（保持纯 Python 标准库）
- 不实现 MCP 工具或 task-driver 集成
- 不改变现有的 CLI 命令接口（只增加新命令或优化输出）
- 不涉及安全、权限、发布、迁移等高风险领域

## Proposed Design

按阶段批量执行，每个阶段完成后验证 TRAICE 评分：

1. **P0 阶段**：文档改进为主，提升规范性（C·规范性 4.2 → 4.8）
2. **P1 阶段**：代码+文档混合，提升可靠性（R·可靠性 4.5 → 4.8）和适用性（A·适用性 4.5 → 4.8）
3. **P2 阶段**：锦上添花，提升有效性（E·有效性 4.5 → 4.8）

每个改进项完成后：
- 更新评分提升计划中的完成状态
- 运行相关测试验证
- 记录证据到执行台账[ledger]

## Alternatives Considered

- **按维度执行**：先完成一个维度的所有改进，再下一个维度。拒绝原因：可能导致某些阶段评分提升不明显，无法验证阶段效果。
- **按依赖顺序执行**：有依赖关系的改进项必须按顺序执行。拒绝原因：评分提升计划已经按优先级分好阶段，依赖关系不明显。

## Acceptance Criteria

| ID | 验收项 | 验证方式 |
|---|---|---|
| AC-1 | P0 阶段 5 项改进全部完成 | 检查 SKILL.md、README.md、项目说明.md 的更新 |
| AC-2 | P1 阶段 16 项改进全部完成 | 检查代码变更、文档更新、测试通过 |
| AC-3 | P2 阶段 4 项改进全部完成 | 检查新命令实现、文档更新 |
| AC-4 | TRAICE 评分达到 4.8 | 按 TRAICE 评分框架逐项验证 |
| AC-5 | 所有改进项有执行证据 | 检查 ledger 中的 TaskResult 和 evidence |
| AC-6 | 现有功能无回归 | 运行现有测试，验证 CLI 命令正常工作 |

## Constraints

- 纯 Python 标准库，零外部依赖
- 保持向后兼容，不破坏现有 CLI 接口
- 文档使用中文，代码和配置保持英文
- 每个改进项必须有可验证的验收标准
- 按阶段批量执行，P0 完成后再做 P1，P1 完成后再做 P2

## Risks

- **风险1**：改进项之间可能存在隐含依赖，导致执行顺序调整
  - 缓解：执行前逐项检查依赖关系，必要时调整顺序
- **风险2**：某些改进项可能影响现有功能
  - 缓解：每个改进项完成后运行回归测试
- **风险3**：评分标准可能存在主观性，导致评分不准确
  - 缓解：按 TRAICE 评分框架逐项验证，确保客观性

## SpecPacket

```yaml
spec_path: docs/task-driver/specs/2026-07-07--traice-score-improvement.md
goal: 完成 forge-memory 评分提升计划的全部 25 项改进，将 TRAICE 评分从 4.5 提升到 4.8
acceptance_criteria:
  - id: AC-1
    description: P0 阶段 5 项改进全部完成
    verification: 检查 SKILL.md、README.md、项目说明.md 的更新
  - id: AC-2
    description: P1 阶段 16 项改进全部完成
    verification: 检查代码变更、文档更新、测试通过
  - id: AC-3
    description: P2 阶段 4 项改进全部完成
    verification: 检查新命令实现、文档更新
  - id: AC-4
    description: TRAICE 评分达到 4.8
    verification: 按 TRAICE 评分框架逐项验证
  - id: AC-5
    description: 所有改进项有执行证据
    verification: 检查 ledger 中的 TaskResult 和 evidence
  - id: AC-6
    description: 现有功能无回归
    verification: 运行现有测试，验证 CLI 命令正常工作
constraints:
  - 纯 Python 标准库，零外部依赖
  - 保持向后兼容，不破坏现有 CLI 接口
  - 文档使用中文，代码和配置保持英文
  - 每个改进项必须有可验证的验收标准
  - 按阶段批量执行，P0 完成后再做 P1，P1 完成后再做 P2
quality_level: production
approved_by_user: true
status: approved
```
