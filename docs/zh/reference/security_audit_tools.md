# Security Audit Tools

## 目标

用 `SecurityAuditToolSet` 在 QitOS 上构建“面向开发者、面向代码库”的漏洞审计 agent。

它和进攻型安全工具的定位不同：

- 面向仓库，而不是面向远程目标
- 以证据采集为主，而不是利用验证为主
- 适合和 `CodingToolSet`、`TaskToolSet` 组合使用

## 提供什么

`SecurityAuditToolSet` 提供一组原子化审计工具：

- `audit_inventory`
- `audit_entrypoints`
- `audit_sink_scan`
- `audit_secret_scan`
- `audit_config_scan`
- `audit_dependency_inventory`
- `audit_dependency_audit`（可选外部扫描）
- `audit_notes_scan`
- `audit_hotspots`

候选 finding 统一使用如下字段：

- `title`
- `category`
- `severity`
- `confidence`
- `file`
- `line`
- `evidence`
- `rationale`
- `recommendation`
- `tags`

## 典型组合方式

一个实用的审计 agent 通常会组合：

- `SecurityAuditToolSet`：安全证据采集
- `CodingToolSet`：代码与文件查看
- `TaskToolSet`：任务规划与分解
- `SECURITY_AUDIT_SYSTEM_PROMPT`：审计心智预设

示例：

```python
from qitos import ToolRegistry
from qitos.kit import CodingToolSet, SECURITY_AUDIT_SYSTEM_PROMPT, SecurityAuditToolSet, TaskToolSet

registry = ToolRegistry()
registry.register_toolset(SecurityAuditToolSet(workspace_root="./repo"), namespace="")
registry.register_toolset(CodingToolSet(workspace_root="./repo"), namespace="")
registry.register_toolset(TaskToolSet(workspace_root="./repo"), namespace="")
```

builder 快捷方式：

```python
from qitos.kit.tool import security_audit_tools

registry = security_audit_tools("./repo", include_external=False)
```

## 外部扫描器

只有在 `include_external=True` 时，`audit_dependency_audit` 才会注册。

当环境里存在对应工具时，它会按顺序尝试：

- `pip-audit`
- `npm audit --json`
- `osv-scanner`

如果都没有安装，它会返回 `status="unavailable"`，而不是直接报错。

## 示例

- `examples/real/code_security_audit_agent.py`
