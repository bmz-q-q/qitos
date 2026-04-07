"""Deprecated compatibility shim for the experimental security audit toolset."""

from __future__ import annotations

import warnings
from typing import Any

from qitos.kit.tool.experimental.security_research import security_audit_tools as _security_audit_tools
from qitos.kit.tool.experimental.security_research.security_audit import SecurityAuditToolSet as _SecurityAuditToolSet


class SecurityAuditToolSet(_SecurityAuditToolSet):
    def __init__(self, *args: Any, **kwargs: Any):
        warnings.warn(
            "qitos.kit.tool.security_audit is deprecated; import SecurityAuditToolSet from "
            "qitos.kit.tool.experimental.security_research instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


def security_audit_tools(*args: Any, **kwargs: Any):
    warnings.warn(
        "qitos.kit.tool.security_audit_tools is deprecated; import security_research_tools or "
        "security_audit_tools from qitos.kit.tool.experimental.security_research instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _security_audit_tools(*args, **kwargs)


__all__ = ["SecurityAuditToolSet", "security_audit_tools"]
