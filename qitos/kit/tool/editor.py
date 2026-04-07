"""Deprecated editor toolset adapters backed by the canonical coding toolset."""

from __future__ import annotations

import warnings
from typing import Any, Dict, List

from qitos.kit.tool.coding import CodingToolSet


class EditorToolSet:
    """Deprecated adapter for the legacy editor toolset API."""

    name = "editor"
    version = "2"

    def __init__(self, workspace_root: str = "."):
        warnings.warn(
            "EditorToolSet is deprecated; use CodingToolSet or coding_tools() instead.",
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
            profile="editor",
        )
        self.view = self._delegate.view
        self.create = self._delegate.create
        self.str_replace = self._delegate.str_replace
        self.insert = self._delegate.insert
        self.search = self._delegate.search
        self.list_tree = self._delegate.list_tree
        self.replace_lines = self._delegate.replace_lines

    def setup(self, context: Dict[str, Any]) -> None:
        self._delegate.setup(context)

    def teardown(self, context: Dict[str, Any]) -> None:
        self._delegate.teardown(context)

    def tools(self) -> List[Any]:
        return [
            self.view,
            self.create,
            self.str_replace,
            self.insert,
            self.search,
            self.list_tree,
            self.replace_lines,
        ]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)


__all__ = ["EditorToolSet"]
