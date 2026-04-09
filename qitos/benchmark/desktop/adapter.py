"""OSWorld-compatible starter task pack for the official desktop benchmark path."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from qitos.core import EnvSpec, Task, TaskBudget

from ..base import BenchmarkAdapter, BenchmarkSource


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class DesktopTaskSpec:
    task_id: str
    split: str
    instruction: str
    screenshot_path: str
    completion_contract: dict[str, Any] = field(default_factory=dict)
    accessibility_tree: Any = None
    dom: Any = None
    ocr: list[dict[str, Any]] = field(default_factory=list)
    ui_candidates: list[dict[str, Any]] = field(default_factory=list)
    terminal: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(
        default_factory=lambda: ["gui_observer", "gui_controller"]
    )
    evaluation_hooks: dict[str, Any] = field(default_factory=dict)

    def to_task(self) -> Task:
        screenshot_path = Path(self.screenshot_path)
        if not screenshot_path.is_absolute():
            screenshot_path = (_repo_root() / screenshot_path).resolve()
        metadata = {
            "lane": "desktop_benchmark",
            "task_kind": "osworld_compatible_starter",
            "completion_contract": dict(self.completion_contract or {}),
            "evaluation_hooks": dict(self.evaluation_hooks or {}),
            **dict(self.metadata or {}),
        }
        env_config = {
            "provider": "mock",
            "instruction": self.instruction,
            "screenshot_path": str(screenshot_path),
            "accessibility_tree": self.accessibility_tree,
            "dom": self.dom,
            "ocr": list(self.ocr or []),
            "ui_candidates": list(self.ui_candidates or []),
            "terminal": self.terminal,
            "metadata": metadata,
        }
        return Task(
            id=self.task_id,
            objective=self.instruction,
            env_spec=EnvSpec(
                type="desktop",
                config=env_config,
                capabilities=list(self.capabilities or []),
                metadata={"benchmark_family": "desktop"},
            ),
            budget=TaskBudget(max_steps=8),
            metadata=metadata,
            success_criteria=[
                str(x)
                for x in (self.completion_contract or {}).get("criteria", [])
                if str(x).strip()
            ],
        )


class DesktopStarterAdapter(BenchmarkAdapter):
    source = BenchmarkSource(
        name="desktop-starter", split="starter", subset="osworld-starter"
    )

    def __init__(self, dataset_path: str | None = None):
        default_path = (
            Path(__file__).resolve().parent / "data" / "starter_tasks.json"
        )
        self.dataset_path = Path(dataset_path or default_path).expanduser().resolve()

    def load_records(self, split: str = "starter") -> list[dict[str, Any]]:
        payload = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        rows = list(payload.get("tasks") or [])
        return [row for row in rows if str(row.get("split") or "starter") == split]

    def to_tasks(
        self,
        records: Iterable[Mapping[str, Any]],
        split: str,
        limit: Optional[int] = None,
    ) -> list[Task]:
        tasks: list[Task] = []
        for row in records:
            spec = DesktopTaskSpec(
                task_id=str(row.get("task_id") or row.get("id") or "desktop_task"),
                split=str(row.get("split") or split),
                instruction=str(row.get("instruction") or row.get("objective") or ""),
                screenshot_path=str(row.get("screenshot_path") or ""),
                completion_contract=dict(row.get("completion_contract") or {}),
                accessibility_tree=row.get("accessibility_tree"),
                dom=row.get("dom"),
                ocr=list(row.get("ocr") or []),
                ui_candidates=list(row.get("ui_candidates") or []),
                terminal=str(row.get("terminal") or ""),
                metadata=dict(row.get("metadata") or {}),
                capabilities=list(row.get("capabilities") or ["gui_observer", "gui_controller"]),
                evaluation_hooks=dict(row.get("evaluation_hooks") or {}),
            )
            tasks.append(spec.to_task())
            if limit is not None and len(tasks) >= int(limit):
                break
        return tasks


def load_desktop_tasks(
    *, split: str = "starter", limit: Optional[int] = None, root: Optional[str] = None
) -> list[Task]:
    adapter = DesktopStarterAdapter(dataset_path=root)
    return adapter.to_tasks(adapter.load_records(split=split), split=split, limit=limit)
