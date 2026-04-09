"""Built-in runner for the official OSWorld benchmark family."""

from __future__ import annotations

from pathlib import Path

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec, Task
from qitos.recipes.desktop import build_benchmark_result, execute_desktop_task

from ..contracts import PreparedBenchmarkTask
from .evaluator import OSWorldEvaluator
from .runtime import OSWorldRuntimeHook
from .scorer import OSWorldScorer


def run_osworld_task(
    *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
) -> BenchmarkRunResult:
    settings = dict((task.metadata or {}).get("osworld_settings") or {})
    runtime_hook = OSWorldRuntimeHook(
        repo_root=str((run_spec.environment or {}).get("repo_root") or ""),
        settings=settings,
    )
    prepared = PreparedBenchmarkTask(task=task, runtime_metadata={})
    execution = None
    error: Exception | None = None
    try:
        prepared = runtime_hook.prepare(
            task=task,
            run_spec=run_spec,
            experiment_spec=experiment_spec,
        )
        execution = execute_desktop_task(
            task=prepared.task,
            run_spec=run_spec,
            experiment_spec=experiment_spec,
            workspace=Path("./playground/osworld") / str(prepared.task.id),
            smoke=bool((run_spec.metadata or {}).get("osworld_smoke", False)),
            render=False,
            trace=True,
            trace_logdir=str((run_spec.environment or {}).get("trace_logdir") or "./runs"),
            max_steps=int(prepared.task.budget.max_steps or 15),
        )
        base_result = build_benchmark_result(execution, benchmark_name="osworld")
        evaluator = OSWorldEvaluator(
            reference_root=str((run_spec.environment or {}).get("osworld_reference_root") or ""),
            eval_cache_root=str((run_spec.environment or {}).get("osworld_eval_cache_root") or ".qitos/osworld_eval_cache"),
        )
        evaluation = evaluator.evaluate(
            prepared=prepared,
            run_spec=run_spec,
            experiment_spec=experiment_spec,
            execution=execution,
        )
        result = OSWorldScorer().score(
            prepared=prepared,
            run_spec=run_spec,
            experiment_spec=experiment_spec,
            execution=execution,
            evaluation=evaluation,
            base_result=base_result,
        )
        result.metadata = {
            **dict(result.metadata or {}),
            "benchmark_runtime": dict(prepared.runtime_metadata or {}),
            "family": "osworld",
        }
        return result
    except Exception as exc:
        error = exc
        fallback = BenchmarkRunResult(
            task_id=str(task.id),
            benchmark="osworld",
            split=str(experiment_spec.benchmark_split or run_spec.benchmark_split or "test"),
            prediction=None,
            success=False,
            stop_reason="benchmark_error",
            steps=0,
            latency_seconds=0.0,
            token_usage=0,
            cost=0.0,
            trace_run_dir=None,
            run_spec_ref=run_spec.fingerprint(),
            metadata={
                "benchmark_runtime": dict(prepared.runtime_metadata or {}),
                "error": str(exc),
            },
        )
        return fallback
    finally:
        finalize = runtime_hook.finalize(
            prepared=prepared,
            run_spec=run_spec,
            experiment_spec=experiment_spec,
            execution=execution,
            error=error,
        )
        if execution is not None and getattr(execution, "result", None) is not None:
            task_result = getattr(execution.result, "task_result", None)
            if task_result is not None and isinstance(getattr(task_result, "metadata", None), dict):
                task_result.metadata["benchmark_finalize"] = dict(finalize or {})


def attach_runtime_metadata(
    *, prepared: PreparedBenchmarkTask, row: BenchmarkRunResult
) -> BenchmarkRunResult:
    payload = BenchmarkRunResult.from_value(row)
    payload.metadata = {
        **dict(payload.metadata or {}),
        "benchmark_runtime": dict(prepared.runtime_metadata or {}),
    }
    return payload


__all__ = ["attach_runtime_metadata", "run_osworld_task"]
