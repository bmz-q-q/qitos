"""GAIA benchmark runtime hooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from qitos.core import ExperimentSpec, RunSpec, Task

from ..contracts import BenchmarkRuntimeHook, PreparedBenchmarkTask


@dataclass
class GaiaRuntimeHook(BenchmarkRuntimeHook):
    """Lightweight runtime hook for GAIA benchmark runs."""

    def prepare(
        self, *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
    ) -> PreparedBenchmarkTask:
        metadata: Dict[str, Any] = {
            "benchmark": "gaia",
            "split": str(experiment_spec.benchmark_split or run_spec.benchmark_split or "validation"),
            "reference_answer": (task.metadata or {}).get("reference_answer"),
            "attachments": list((task.inputs or {}).get("attachments") or []),
        }
        return PreparedBenchmarkTask(task=task, runtime_metadata=metadata)

