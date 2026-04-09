"""Adapter layer that maps OSWorld datasets into canonical QitOS tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from qitos.core import EnvSpec, Task, TaskBudget

from ..base import BenchmarkAdapter, BenchmarkSource


def _default_dataset_path() -> str:
    return str(
        (Path(__file__).resolve().parents[3] / "references" / "OSWorld" / "evaluation_examples").resolve()
    )


@dataclass(frozen=True)
class OSWorldBenchmarkAdapter(BenchmarkAdapter):
    dataset_path: str = _default_dataset_path()
    name: str = "osworld"
    description: str = "OSWorld benchmark adapter."
    split_field: str = "split"
    default_split: str = "test"
    test_all_meta_path: str = "test_all.json"
    source: BenchmarkSource = field(
        default_factory=lambda: BenchmarkSource(name="osworld", split="test")
    )

    def _dataset_root(self) -> Path:
        root = Path(self.dataset_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"OSWorld dataset path not found: {root}")
        return root

    def _read_json(self, path: Path, *, invalid_message: str) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise ValueError(f"{invalid_message}: {path}") from exc

    def _test_all(self) -> dict[str, list[str]]:
        root = self._dataset_root()
        path = root / self.test_all_meta_path
        data = self._read_json(path, invalid_message="OSWorld test_all format invalid")
        out: dict[str, list[str]] = {}
        for domain, ids in data.items():
            if not isinstance(ids, list):
                continue
            out[str(domain)] = [str(x) for x in ids]
        return out

    def load_records(
        self,
        *,
        split: Optional[str] = None,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        root = self._dataset_root()
        selected_split = str(split or self.default_split)
        for current_domain, ids in self._test_all().items():
            if domain and str(domain) != current_domain:
                continue
            for example_id in ids:
                file_path = root / "examples" / current_domain / f"{example_id}.json"
                if not file_path.exists():
                    continue
                example = self._read_json(
                    file_path, invalid_message="OSWorld example format invalid"
                )
                row_split = str(example.get(self.split_field) or self.default_split)
                if row_split != selected_split:
                    continue
                rows.append(
                    {
                        "domain": current_domain,
                        "example_id": example_id,
                        "file_path": file_path,
                        "example": example,
                    }
                )
                if limit is not None and len(rows) >= int(limit):
                    return rows
        return rows

    def to_tasks(
        self,
        records: Iterable[Mapping[str, Any]],
        split: str,
        limit: Optional[int] = None,
    ) -> list[Task]:
        tasks: list[Task] = []
        for row in records:
            task = self._row_to_task(dict(row), split=split)
            if task is None:
                continue
            tasks.append(task)
            if limit is not None and len(tasks) >= int(limit):
                break
        return tasks

    def _row_to_task(self, row: Mapping[str, Any], *, split: str) -> Task | None:
        domain = str(row.get("domain") or "")
        example_id = str(row.get("example_id") or "")
        file_path = Path(str(row.get("file_path") or ""))
        example = dict(row.get("example") or {})
        instruction = str(example.get("instruction") or "").strip()
        if not instruction:
            return None
        task_id = f"osworld-{domain}-{example_id}"
        metadata = {
            "osworld_settings": dict(example.get("osworld_settings") or {}),
            "benchmark": "osworld",
            "domain": domain,
            "example_id": example_id,
            "sample_identity": f"osworld:{domain}:{example_id}",
            "osworld_task_id": str(example.get("id") or example_id),
            "split": split,
            "instruction": instruction,
            "snapshot": example.get("snapshot"),
            "proxy": bool(example.get("proxy", False)),
            "related_apps": list(example.get("related_apps") or []),
            "config": list(example.get("config") or []),
            "trajectory": list(example.get("trajectory") or []),
            "evaluator": example.get("evaluator"),
            "source": example.get("source"),
            "example_path": str(file_path),
            "task_config": dict(example),
            "runtime_container": {
                "benchmark": "osworld",
                "provider_name": "osworld",
                "requires_container": True,
                "cleanup_policy": "destroy_on_release",
                "startup": dict(example.get("osworld_settings") or {}),
            },
        }
        return Task(
            id=task_id,
            objective=instruction,
            env_spec=EnvSpec(
                type="desktop",
                config={
                    "provider": "container",
                    "instruction": instruction,
                    "metadata": {
                        "benchmark": "osworld",
                        "domain": domain,
                        "example_id": example_id,
                    },
                },
                capabilities=["gui_observer", "gui_controller"],
                metadata={"benchmark_family": "osworld"},
            ),
            budget=TaskBudget(max_steps=15),
            metadata=metadata,
            success_criteria=["Execute the OSWorld task and satisfy the benchmark evaluator."],
        )


def load_osworld_tasks(
    *,
    split: str = "test",
    limit: Optional[int] = None,
    root: Optional[str] = None,
    domain: Optional[str] = None,
) -> list[Task]:
    adapter = OSWorldBenchmarkAdapter(dataset_path=str(root or _default_dataset_path()))
    records = adapter.load_records(split=split, domain=domain, limit=limit)
    return adapter.to_tasks(records, split=split, limit=limit)


__all__ = ["OSWorldBenchmarkAdapter", "load_osworld_tasks"]
