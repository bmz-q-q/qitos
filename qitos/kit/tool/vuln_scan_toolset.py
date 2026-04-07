"""Deprecated compatibility shim for experimental vulnerability scanning tools."""

from __future__ import annotations

import warnings
from typing import Any

from qitos.kit.tool.experimental.security_research.vuln_scan_toolset import VulnScanToolSet as _VulnScanToolSet


class VulnScanToolSet(_VulnScanToolSet):
    def __init__(self, *args: Any, **kwargs: Any):
        warnings.warn(
            "qitos.kit.tool.vuln_scan_toolset is deprecated; import VulnScanToolSet from "
            "qitos.kit.tool.experimental.security_research instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["VulnScanToolSet"]
