"""CyBench evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from qitos.core import ExperimentSpec, RunSpec

from ..contracts import BenchmarkEvaluator, PreparedBenchmarkTask


@dataclass
class CyBenchEvaluatorBridge(BenchmarkEvaluator):
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
            "guided_subtask_score": float(getattr(execution, "guided_subtask_score", 0.0) or 0.0),
            "guided_final_score": float(getattr(execution, "guided_final_score", 0.0) or 0.0),
            "unguided_success": bool(getattr(execution, "unguided_success", False)),
            "partial_matches": list(getattr(execution, "partial_matches", []) or []),
            "success": bool(getattr(execution, "success", False)),
        }
