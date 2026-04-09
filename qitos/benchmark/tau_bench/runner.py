"""Built-in runner for the official Tau-Bench benchmark family."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec, Task
from qitos.recipes.benchmarks.tau_bench import (
    build_tau_benchmark_result,
    execute_tau_task,
)

from .evaluator import TauBenchEvaluator
from .runtime import TauBenchRuntimeHook
from .scorer import TauBenchScorer


def run_tau_bench_task(
    *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
) -> BenchmarkRunResult:
    args = _build_args(run_spec=run_spec, experiment_spec=experiment_spec)
    runtime_hook = TauBenchRuntimeHook(env_name=args.tau_env, split=args.tau_split)
    prepared = runtime_hook.prepare(
        task=task,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    execution = execute_tau_task(
        args=args,
        adapter=args.adapter,
        idx=int(prepared.runtime_metadata.get("task_index", 0) or 0),
        record=dict((task.metadata or {}).get("raw_record") or {}),
        root=Path(str((run_spec.environment or {}).get("workspace") or "./playground/tau_bench")),
        trial=0,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    base_result = build_tau_benchmark_result(execution)
    evaluation = TauBenchEvaluator().evaluate(
        prepared=prepared,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
        execution=execution,
    )
    result = TauBenchScorer().score(
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
        "family": "tau-bench",
    }
    return result


def _build_args(*, run_spec: RunSpec, experiment_spec: ExperimentSpec) -> Namespace:
    from .adapter import TauBenchAdapter

    env_name = str(
        (run_spec.environment or {}).get("tau_env")
        or (experiment_spec.benchmark_metadata or {}).get("subset")
        or "retail"
    )
    split = str(experiment_spec.benchmark_split or run_spec.benchmark_split or "test")
    args = Namespace(
        workspace=str((run_spec.environment or {}).get("workspace") or "./playground/tau_bench"),
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
        max_steps=int((run_spec.metadata or {}).get("max_steps", 30)),
        tau_env=env_name,
        tau_split=split,
        enable_model_judge=False,
    )
    args.adapter = TauBenchAdapter(env_name=env_name, task_split=split)
    return args
