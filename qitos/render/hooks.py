"""Render hook façade with backward-compatible exports."""

from __future__ import annotations

from ._hooks_impl import (
    ClaudeStyleHook,
    RenderHook,
    RenderStreamHook,
    RichConsoleHook,
    SimpleRichConsoleHook,
    VerboseRichConsoleHook,
)

__all__ = [
    "RenderHook",
    "RenderStreamHook",
    "ClaudeStyleHook",
    "RichConsoleHook",
    "SimpleRichConsoleHook",
    "VerboseRichConsoleHook",
]
