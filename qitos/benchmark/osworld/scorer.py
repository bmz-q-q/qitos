"""Benchmark-specific scorer implementation for OSWorld."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec, Task

from ..contracts import BenchmarkScorer, PreparedBenchmarkTask


def _coerce_score(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


@dataclass
class OSWorldScorer(BenchmarkScorer):
    metric_name: str = "accuracy"
    scorer_id: str = "osworld"

    def score(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
        evaluation: dict[str, Any],
        base_result: BenchmarkRunResult,
    ) -> BenchmarkRunResult:
        _ = (prepared, run_spec, experiment_spec, execution)
        score_value = _coerce_score((evaluation or {}).get("score"))
        if score_value is None:
            text = str(base_result.prediction or "").lower()
            if "done" in text and "fail" not in text:
                score_value = 1.0
            elif "success" in text:
                score_value = 1.0
            elif "fail" in text:
                score_value = 0.0
            else:
                score_value = 0.0
        score_value = max(0.0, min(1.0, float(score_value)))
        payload = BenchmarkRunResult.from_value(base_result)
        payload.success = bool(score_value >= 1.0)
        payload.metadata = {
            **dict(payload.metadata or {}),
            "osworld_score": score_value,
            "score_metric": self.metric_name,
            "evaluation": dict(evaluation or {}),
        }
        return payload


def score_osworld_result(
    *,
    task: Task,
    run_spec: RunSpec,
    experiment_spec: ExperimentSpec,
    execution: Any,
    evaluation: dict[str, Any],
    base_result: BenchmarkRunResult,
) -> BenchmarkRunResult:
    _ = (task, run_spec, experiment_spec, execution)
    return OSWorldScorer().score(
        prepared=PreparedBenchmarkTask(task=task),
        run_spec=run_spec,
        experiment_spec=experiment_spec,
        execution=execution,
        evaluation=evaluation,
        base_result=base_result,
    )


__all__ = ["OSWorldScorer", "score_osworld_result"]
