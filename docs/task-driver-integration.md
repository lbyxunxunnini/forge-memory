# Task Driver Integration

Forge Memory 与任务驱动框架的集成点是计划阶段（v0.4）。

## 集成目标

```text
任务驱动框架收到用户任务
  -> 计划阶段调用 Forge Memory
  -> 获取 context_pack
  -> 基于上下文包生成文件映射、风险点和验证范围
```

## MCP 工具

第一批 MCP 工具只保留 3 个：

```text
forge_memory_scan_project
forge_memory_get_context
forge_memory_analyze_impact
```

### forge_memory_get_context

请求：

```json
{
  "repo_root": "/path/to/project",
  "task": "修改订阅管理入口",
  "mode": "planning",
  "entry_files": [
    "lib/pages/subscription/subscription_page.dart"
  ]
}
```

响应：

```json
{
  "repo_root": "/path/to/project",
  "task": "修改订阅管理入口",
  "mode": "planning",
  "related_files": [],
  "related_modules": [],
  "recent_changes": [],
  "relations": [],
  "risk_points": [],
  "suggested_tests": [],
  "confidence": {
    "overall": "medium",
    "reasons": []
  },
  "context_pack": "markdown..."
}
```

## 计划阶段规则

任务驱动框架启用 Forge Memory 后：

- 写计划前必须调用 `forge_memory_get_context`。
- 计划的文件映射优先来自 `related_files`，但仍需源码验证。
- 验证计划必须参考 `suggested_tests`。
- 风险段必须纳入 `risk_points`。
- 如果 Forge Memory 不可用，必须记录降级路径。

降级记录示例：

```yaml
mode: degraded-single-skill
reason: forge_memory_get_context unavailable
fallback: targeted project scan
evidence_strength_limit: medium
```

## 上下文包 Markdown 结构

```md
# Forge Memory Context Pack

## Task

## Likely Entry Files

## Related Modules

## Recent Changes

## Dependency / Impact

## Risk Points

## Suggested Tests

## Evidence And Caveats
```

## 执行台账证据

任务驱动框架应在执行台账中记录：

```yaml
- timestamp: 2026-07-06T10:00:00+08:00
  command: forge_memory_get_context
  exit_code: 0
  output_excerpt: "related_files=8 suggested_tests=4 confidence=medium"
  covers_requirement_ids: [AC-1]
  strength: medium
```

## 不能做的事

- 不允许把 Forge Memory 的推断当作源码事实。
- 不允许因为拿到 `context_pack` 就跳过源码验证。
- 不允许 Forge Memory 不可用时静默回退。
- 不允许任务驱动框架直接依赖内部 JSONL 表结构。
