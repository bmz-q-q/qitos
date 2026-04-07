"""Deprecated file tool adapters that route through env filesystem ops."""

from __future__ import annotations

import warnings
from typing import Any, Dict, Optional

from qitos.core.tool import BaseTool, ToolPermission, ToolSpec


def _get_file_ops(runtime_context: Optional[Dict[str, Any]]) -> Any:
    runtime_context = runtime_context or {}
    ops = runtime_context.get("ops", {})
    return ops.get("file")


class WriteFile(BaseTool):
    """Write text content to a file under the workspace root.

    :param filename: Path relative to the workspace root.
    :param content: Full text content to write into the file.
    :param runtime_context: Optional runtime context carrying env file ops.

    Requires env filesystem ops so the runtime can enforce workspace scope.
    """

    def __init__(self, root_dir: str = "."):
        _ = root_dir
        warnings.warn(
            "WriteFile is deprecated; use env-backed file tools or CodingToolSet.write_file instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            ToolSpec(
                name="write_file",
                description="Write text content to a file under the workspace root.",
                parameters={"filename": {"type": "string"}, "content": {"type": "string"}},
                required=["filename", "content"],
                permissions=ToolPermission(filesystem_write=True),
                required_ops=["file"],
            )
        )

    def execute(self, args: Dict[str, Any], runtime_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Write text content to a file under the workspace root.

        :param filename: Path relative to the workspace root.
        :param content: Full text content to write into the file.
        :param runtime_context: Optional runtime context carrying env file ops.

        Requires env filesystem ops so the runtime can enforce workspace scope.
        """
        filename = str(args.get("filename", ""))
        content = str(args.get("content", ""))
        file_ops = _get_file_ops(runtime_context)
        if file_ops is None:
            return {"status": "error", "message": "Missing file ops", "path": filename}
        try:
            file_ops.write_text(filename, content)
            return {"status": "success", "path": filename, "size": len(content)}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "path": filename}


class ReadFile(BaseTool):
    """Read text content from a file under the workspace root.

    :param filename: Path relative to the workspace root.
    :param runtime_context: Optional runtime context carrying env file ops.

    Requires env filesystem ops so the runtime can enforce workspace scope.
    """

    def __init__(self, root_dir: str = "."):
        _ = root_dir
        warnings.warn(
            "ReadFile is deprecated; use env-backed file tools or CodingToolSet.read_file instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            ToolSpec(
                name="read_file",
                description="Read text content from a file under the workspace root.",
                parameters={"filename": {"type": "string"}},
                required=["filename"],
                permissions=ToolPermission(filesystem_read=True),
                required_ops=["file"],
                read_only=True,
            )
        )

    def execute(self, args: Dict[str, Any], runtime_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Read text content from a file under the workspace root.

        :param filename: Path relative to the workspace root.
        :param runtime_context: Optional runtime context carrying env file ops.

        Requires env filesystem ops so the runtime can enforce workspace scope.
        """
        filename = str(args.get("filename", ""))
        file_ops = _get_file_ops(runtime_context)
        if file_ops is None:
            return {"status": "error", "message": "Missing file ops", "path": filename}
        try:
            content = file_ops.read_text(filename)
            return {"status": "success", "path": filename, "content": content}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "path": filename}


class ListFiles(BaseTool):
    """List files under one directory inside the workspace root.

    :param path: Directory path relative to the workspace root.
    :param limit: Maximum number of returned files.
    :param runtime_context: Optional runtime context carrying env file ops.

    Requires env filesystem ops so the runtime can enforce workspace scope.
    """

    def __init__(self, root_dir: str = "."):
        _ = root_dir
        warnings.warn(
            "ListFiles is deprecated; use env-backed file tools or CodingToolSet.list_files instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            ToolSpec(
                name="list_files",
                description="List files under one directory inside the workspace root.",
                parameters={"path": {"type": "string"}, "limit": {"type": "integer"}},
                required=[],
                permissions=ToolPermission(filesystem_read=True),
                required_ops=["file"],
                read_only=True,
            )
        )

    def execute(self, args: Dict[str, Any], runtime_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List files under one directory inside the workspace root.

        :param path: Directory path relative to the workspace root.
        :param limit: Maximum number of returned files.
        :param runtime_context: Optional runtime context carrying env file ops.

        Requires env filesystem ops so the runtime can enforce workspace scope.
        """
        path = str(args.get("path", "."))
        limit = int(args.get("limit", 200))
        file_ops = _get_file_ops(runtime_context)
        if file_ops is None:
            return {"status": "error", "message": "Missing file ops", "path": path}
        try:
            files = file_ops.list_files(path, limit=limit)
            return {"status": "success", "path": path, "count": len(files), "files": files}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "path": path}


__all__ = ["WriteFile", "ReadFile", "ListFiles"]
