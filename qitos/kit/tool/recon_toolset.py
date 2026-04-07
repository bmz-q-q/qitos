"""Deprecated compatibility shim for experimental reconnaissance tools."""

from __future__ import annotations

import warnings
from typing import Any

from qitos.kit.tool.experimental.security_research.recon_toolset import ReconToolSet as _ReconToolSet


class ReconToolSet(_ReconToolSet):
    def __init__(self, *args: Any, **kwargs: Any):
        warnings.warn(
            "qitos.kit.tool.recon_toolset is deprecated; import ReconToolSet from "
            "qitos.kit.tool.experimental.security_research instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["ReconToolSet"]
