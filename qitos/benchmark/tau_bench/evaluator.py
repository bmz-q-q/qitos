"""Tau-Bench evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from qitos.core import ExperimentSpec, RunSpec

from ..contracts import BenchmarkEvaluator, PreparedBenchmarkTask


@dataclass
class TauBenchEvaluator(BenchmarkEvaluator):
    def evaluate(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
    ) -> Dict[str, Any]:
        _ = (prepared, run_spec, experiment_spec)
        return {
            "reward": float(getattr(execution, "reward", 0.0) or 0.0),
            "score": float(getattr(execution, "eval_score", 0.0) or 0.0),
            "details": list(getattr(execution, "eval_details", []) or []),
            "success": bool(getattr(execution, "eval_score", 0.0) >= 1.0),
        }
