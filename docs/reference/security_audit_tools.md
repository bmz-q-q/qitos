# Security Audit Tools

## Goal

Use `SecurityAuditToolSet` to build developer-facing codebase vulnerability audit agents on top of QitOS.

This preset is intentionally different from offensive security tooling:

- it is repository-focused, not target-focused
- it is evidence-first, not exploit-first
- it is designed to compose with `CodingToolSet` and `TaskToolSet`

## What it provides

`SecurityAuditToolSet` exposes a small set of atomic audit tools:

- `audit_inventory`
- `audit_entrypoints`
- `audit_sink_scan`
- `audit_secret_scan`
- `audit_config_scan`
- `audit_dependency_inventory`
- `audit_dependency_audit` (optional external scanners)
- `audit_notes_scan`
- `audit_hotspots`

All candidate findings use the same shape:

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

## Typical composition

For a practical audit agent, combine:

- `SecurityAuditToolSet`: security evidence collection
- `CodingToolSet`: direct code inspection helpers
- `TaskToolSet`: external task planning / decomposition
- `SECURITY_AUDIT_SYSTEM_PROMPT`: audit-specific model prior

Example:

```python
from qitos import ToolRegistry
from qitos.kit import CodingToolSet, SECURITY_AUDIT_SYSTEM_PROMPT, SecurityAuditToolSet, TaskToolSet

registry = ToolRegistry()
registry.register_toolset(SecurityAuditToolSet(workspace_root="./repo"), namespace="")
registry.register_toolset(CodingToolSet(workspace_root="./repo"), namespace="")
registry.register_toolset(TaskToolSet(workspace_root="./repo"), namespace="")
```

Builder shortcut:

```python
from qitos.kit.tool import security_audit_tools

registry = security_audit_tools("./repo", include_external=False)
```

## External scanners

`audit_dependency_audit` is only registered when `include_external=True`.

It will try the supported dependency auditors in this order when available:

- `pip-audit`
- `npm audit --json`
- `osv-scanner`

If none are installed, the tool returns `status="unavailable"` instead of failing the run.

## Example

- `examples/real/code_security_audit_agent.py`
