"""CyBench scorer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec

from ..contracts import BenchmarkScorer, PreparedBenchmarkTask


@dataclass
class CyBenchScorer(BenchmarkScorer):
    metric_name: str = "guided_subtask_score"
    scorer_id: str = "cybench"

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
        payload = BenchmarkRunResult.from_value(base_result)
        payload.success = bool((evaluation or {}).get("success", False))
        payload.metadata = {
            **dict(payload.metadata or {}),
            "score_metric": self.metric_name,
            "evaluation": dict(evaluation or {}),
        }
        return payload
