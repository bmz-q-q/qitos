"""Deprecated compatibility shim for experimental password tooling."""

from __future__ import annotations

import warnings
from typing import Any

from qitos.kit.tool.experimental.security_research.password_toolset import PasswordToolSet as _PasswordToolSet


class PasswordToolSet(_PasswordToolSet):
    def __init__(self, *args: Any, **kwargs: Any):
        warnings.warn(
            "qitos.kit.tool.password_toolset is deprecated; import PasswordToolSet from "
            "qitos.kit.tool.experimental.security_research instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["PasswordToolSet"]
