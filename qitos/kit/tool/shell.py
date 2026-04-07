"""Deprecated shell tool adapter backed by the canonical coding toolset."""

from __future__ import annotations

import warnings
from copy import deepcopy
from typing import Any, Dict, Optional

from qitos.core.tool import BaseTool, FunctionTool, ToolPermissionDecision, ToolValidationResult
from qitos.kit.tool.coding import CodingToolSet


class RunCommand(BaseTool):
    """Deprecated adapter for the legacy run_command tool."""

    def __init__(self, timeout: int = 30, cwd: str = ".", env: Optional[Dict[str, str]] = None):
        warnings.warn(
            "RunCommand is deprecated; use CodingToolSet.run_command or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        _ = env
        self._delegate = FunctionTool(
            CodingToolSet(
                workspace_root=cwd,
                shell_timeout=timeout,
                include_notebook=False,
                enable_lsp=False,
                enable_tasks=False,
                enable_web=False,
                expose_modern_names=False,
            ).run_command
        )
        super().__init__(deepcopy(self._delegate.spec))

    def validate_input(
        self,
        args: Dict[str, Any],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> ToolValidationResult:
        return self._delegate.validate_input(args, runtime_context=runtime_context)

    def check_permissions(
        self,
        args: Dict[str, Any],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> ToolPermissionDecision:
        return self._delegate.check_permissions(args, runtime_context=runtime_context)

    def run(self, **kwargs: Any) -> Any:
        return self._delegate.run(**kwargs)

    def call(self, args: Dict[str, Any], runtime_context: Optional[Dict[str, Any]] = None) -> Any:
        return self._delegate.call(args, runtime_context=runtime_context)

    def execute(self, args: Dict[str, Any], runtime_context: Optional[Dict[str, Any]] = None) -> Any:
        return self._delegate.execute(args, runtime_context=runtime_context)


__all__ = ["RunCommand"]
