"""GAIA benchmark scorer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec

from ..contracts import BenchmarkScorer, PreparedBenchmarkTask


@dataclass
class GaiaScorer(BenchmarkScorer):
    metric_name: str = "exact_match"
    scorer_id: str = "gaia"

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
        exact = bool((evaluation or {}).get("exact_match", False))
        payload.success = exact
        payload.metadata = {
            **dict(payload.metadata or {}),
            "score_metric": self.metric_name,
            "evaluation": dict(evaluation or {}),
        }
        return payload

