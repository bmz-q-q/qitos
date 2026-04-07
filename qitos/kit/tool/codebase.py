"""Deprecated codebase tool adapters backed by the canonical coding toolset."""

from __future__ import annotations

import warnings
from copy import deepcopy
from typing import Any, Dict, Optional

from qitos.core.tool import BaseTool, FunctionTool, ToolPermissionDecision, ToolValidationResult
from qitos.kit.tool._workspace import resolve_workspace_path
from qitos.kit.tool.coding import CodingToolSet


class _DelegatingLegacyTool(BaseTool):
    def __init__(self, delegate: Any):
        self._delegate = FunctionTool(delegate)
        super().__init__(deepcopy(self._delegate.spec))
        self.spec.description = str(self._delegate.spec.description)

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


class GlobFiles(_DelegatingLegacyTool):
    """Deprecated adapter for the legacy glob_files tool."""

    def __init__(self, root_dir: str = "."):
        warnings.warn(
            "GlobFiles is deprecated; use CodingToolSet.glob_v2 or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(CodingToolSet(workspace_root=root_dir, expose_modern_names=False).glob_files)


class GrepFiles(_DelegatingLegacyTool):
    """Deprecated adapter for the legacy grep_files tool."""

    def __init__(self, root_dir: str = "."):
        warnings.warn(
            "GrepFiles is deprecated; use CodingToolSet.grep_v2 or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(CodingToolSet(workspace_root=root_dir, expose_modern_names=False).grep_files)


class ReadFileRange(_DelegatingLegacyTool):
    """Deprecated adapter for the legacy read_file_range tool."""

    def __init__(self, root_dir: str = "."):
        warnings.warn(
            "ReadFileRange is deprecated; use CodingToolSet.file_read_v2 or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(CodingToolSet(workspace_root=root_dir, expose_modern_names=False).read_file_range)


class AppendFile(_DelegatingLegacyTool):
    """Deprecated adapter for the legacy append_file tool."""

    def __init__(self, root_dir: str = "."):
        warnings.warn(
            "AppendFile is deprecated; use CodingToolSet.append_file or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(CodingToolSet(workspace_root=root_dir, expose_modern_names=False).append_file)


class MakeDirectory(_DelegatingLegacyTool):
    """Deprecated adapter for the legacy make_directory tool."""

    def __init__(self, root_dir: str = "."):
        warnings.warn(
            "MakeDirectory is deprecated; use CodingToolSet.make_directory or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(CodingToolSet(workspace_root=root_dir, expose_modern_names=False).make_directory)


class CodebaseToolSet:
    """Deprecated adapter for the legacy codebase toolset API."""

    name = "codebase"
    version = "2"

    def __init__(self, workspace_root: str = "."):
        warnings.warn(
            "CodebaseToolSet is deprecated; use CodingToolSet or coding_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._delegate = CodingToolSet(
            workspace_root=workspace_root,
            include_notebook=False,
            enable_lsp=False,
            enable_tasks=False,
            enable_web=False,
            expose_legacy_aliases=True,
            expose_modern_names=False,
            profile="codebase",
        )
        self.glob_files = self._delegate.glob_files
        self.grep_files = self._delegate.grep_files
        self.read_file_range = self._delegate.read_file_range
        self.append_file = self._delegate.append_file
        self.make_directory = self._delegate.make_directory
        for item in self._delegate.tools():
            tool_obj = item if isinstance(item, BaseTool) else FunctionTool(item)
            setattr(self, tool_obj.spec.name, tool_obj)

    def setup(self, context: Dict[str, Any]) -> None:
        self._delegate.setup(context)

    def teardown(self, context: Dict[str, Any]) -> None:
        self._delegate.teardown(context)

    def tools(self) -> list[Any]:
        return [
            self.glob_files,
            self.grep_files,
            self.read_file_range,
            self.append_file,
            self.make_directory,
        ]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)


__all__ = [
    "GlobFiles",
    "GrepFiles",
    "ReadFileRange",
    "AppendFile",
    "MakeDirectory",
    "CodebaseToolSet",
    "_resolve_workspace_path",
]

_resolve_workspace_path = resolve_workspace_path
