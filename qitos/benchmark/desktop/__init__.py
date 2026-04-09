"""Desktop starter benchmark adapters and runners for QitOS v0.5."""

from .adapter import DesktopStarterAdapter, DesktopTaskSpec, load_desktop_tasks
from .runner import run_desktop_starter_task

__all__ = [
    "DesktopStarterAdapter",
    "DesktopTaskSpec",
    "load_desktop_tasks",
    "run_desktop_starter_task",
]
