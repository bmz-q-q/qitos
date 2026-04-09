"""GAIA benchmark evaluator."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict

from qitos.core import ExperimentSpec, RunSpec

from ..contracts import BenchmarkEvaluator, PreparedBenchmarkTask


def _normalize_answer(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


@dataclass
class GaiaEvaluator(BenchmarkEvaluator):
    """Simple exact-match evaluator for GAIA baseline runs."""

    def evaluate(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
    ) -> Dict[str, Any]:
        _ = (run_spec, experiment_spec)
        prediction = getattr(execution, "prediction", None)
        reference = getattr(execution, "reference_answer", None)
        pred_norm = _normalize_answer(prediction)
        ref_norm = _normalize_answer(reference)
        exact = bool(pred_norm and ref_norm and pred_norm == ref_norm)
        return {
            "metric": "exact_match",
            "prediction": prediction,
            "reference_answer": reference,
            "normalized_prediction": pred_norm,
            "normalized_reference_answer": ref_norm,
            "exact_match": exact,
            "has_reference": bool(ref_norm),
            "task_id": str(prepared.task.id),
        }

