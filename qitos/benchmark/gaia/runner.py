"""Built-in runner for the official GAIA benchmark family."""

from __future__ import annotations

from pathlib import Path

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec, Task
from qitos.recipes.benchmarks.gaia import build_gaia_benchmark_result, execute_gaia_task

from .evaluator import GaiaEvaluator
from .runtime import GaiaRuntimeHook
from .scorer import GaiaScorer


def run_gaia_task(
    *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
) -> BenchmarkRunResult:
    runtime_hook = GaiaRuntimeHook()
    prepared = runtime_hook.prepare(
        task=task,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    args = _build_args(run_spec=run_spec, experiment_spec=experiment_spec)
    execution = execute_gaia_task(
        args=args,
        adapter=args.adapter,
        record=dict((task.metadata or {}).get("raw_record") or task.metadata or {}),
        idx=int((task.metadata or {}).get("task_index", 0) or 0),
        root=Path(str((run_spec.environment or {}).get("workspace") or "./playground/gaia")),
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    base_result = build_gaia_benchmark_result(execution)
    evaluation = GaiaEvaluator().evaluate(
        prepared=prepared,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
        execution=execution,
    )
    result = GaiaScorer().score(
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
        "family": "gaia",
    }
    return result


def _build_args(*, run_spec: RunSpec, experiment_spec: ExperimentSpec):
    from argparse import Namespace

    from .adapter import GaiaAdapter

    benchmark_metadata = dict(experiment_spec.benchmark_metadata or {})
    local_dir = str(
        (run_spec.environment or {}).get("gaia_local_dir")
        or (run_spec.environment or {}).get("gaia_dataset_path")
        or "data/gaia"
    )
    args = Namespace(
        workspace=str((run_spec.environment or {}).get("workspace") or "./playground/gaia"),
        model_base_url=str((run_spec.environment or {}).get("base_url") or ""),
        api_key="",
        model_name=str(run_spec.model_name or ""),
        temperature=0.2,
        max_tokens=2048,
        theme="research",
        trace_logdir=str((run_spec.environment or {}).get("trace_logdir") or "./runs"),
        trace_prefix="qitos",
        disable_trace=False,
        disable_render=True,
        max_steps=int((run_spec.metadata or {}).get("max_steps", 16)),
        gaia_split=str(experiment_spec.benchmark_split or run_spec.benchmark_split or "validation"),
        gaia_subset=str(benchmark_metadata.get("subset") or ""),
        gaia_local_dir=local_dir,
        gaia_from_local=True,
        gaia_use_annotated=False,
        gaia_use_raw_dataset=True,
        gaia_download_snapshot=False,
    )
    args.adapter = GaiaAdapter(local_dir=local_dir)
    return args
