"""Benchmark execution extension points shared by benchmark families."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from qitos.core.spec import BenchmarkRunResult, ExperimentSpec, RunSpec
from qitos.core.task import Task


@dataclass
class PreparedBenchmarkTask:
    """Task plus runtime metadata after benchmark-specific preparation."""

    task: Task
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)


class BenchmarkRuntimeHook(ABC):
    """Optional benchmark-specific prepare/finalize lifecycle hook."""

    @abstractmethod
    def prepare(
        self, *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
    ) -> PreparedBenchmarkTask:
        """Prepare task/env-specific runtime inputs before execution."""

    def finalize(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any = None,
        error: Exception | None = None,
    ) -> Dict[str, Any]:
        """Finalize benchmark-specific runtime state after execution."""
        _ = (prepared, run_spec, experiment_spec, execution, error)
        return {}


class BenchmarkEvaluator(ABC):
    """Optional benchmark-specific evaluator producing raw evaluation payloads."""

    @abstractmethod
    def evaluate(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
    ) -> Dict[str, Any]:
        """Evaluate one execution and return benchmark-native payload."""


class BenchmarkScorer(ABC):
    """Optional benchmark-specific scorer mapping evaluation to result fields."""

    @abstractmethod
    def score(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
        evaluation: Dict[str, Any],
        base_result: BenchmarkRunResult,
    ) -> BenchmarkRunResult:
        """Return the final normalized benchmark row."""


def default_prepared_task(task: Task) -> PreparedBenchmarkTask:
    return PreparedBenchmarkTask(task=task, runtime_metadata={})


def merge_runtime_metadata(
    prepared: PreparedBenchmarkTask, extra: Optional[Dict[str, Any]] = None
) -> PreparedBenchmarkTask:
    payload = dict(prepared.runtime_metadata or {})
    if isinstance(extra, dict):
        payload.update(extra)
    return PreparedBenchmarkTask(task=prepared.task, runtime_metadata=payload)


__all__ = [
    "BenchmarkEvaluator",
    "BenchmarkRuntimeHook",
    "BenchmarkScorer",
    "PreparedBenchmarkTask",
    "default_prepared_task",
    "merge_runtime_metadata",
]
