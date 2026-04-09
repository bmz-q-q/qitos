"""Built-in runner for the official CyBench benchmark family."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from qitos.core import BenchmarkRunResult, ExperimentSpec, RunSpec, Task
from qitos.recipes.benchmarks.cybench import (
    build_cybench_benchmark_result,
    execute_cybench_task,
)

from .evaluator import CyBenchEvaluatorBridge
from .runtime import CyBenchRuntimeHook
from .scorer import CyBenchScorer


def run_cybench_task(
    *, task: Task, run_spec: RunSpec, experiment_spec: ExperimentSpec
) -> BenchmarkRunResult:
    args = _build_args(run_spec=run_spec, experiment_spec=experiment_spec)
    runtime_hook = CyBenchRuntimeHook(mode=args.split_mode)
    prepared = runtime_hook.prepare(
        task=task,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    execution = execute_cybench_task(
        args=args,
        adapter=args.adapter,
        idx=int(prepared.runtime_metadata.get("task_index", 0) or 0),
        record=dict((task.metadata or {}).get("raw_record") or {}),
        root=Path(str((run_spec.environment or {}).get("workspace") or "./playground/cybench")),
        trial=0,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
    )
    base_result = build_cybench_benchmark_result(execution)
    evaluation = CyBenchEvaluatorBridge().evaluate(
        prepared=prepared,
        run_spec=run_spec,
        experiment_spec=experiment_spec,
        execution=execution,
    )
    result = CyBenchScorer().score(
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
        "family": "cybench",
    }
    return result


def _build_args(*, run_spec: RunSpec, experiment_spec: ExperimentSpec) -> Namespace:
    from .adapter import CyBenchAdapter

    split_mode = str(experiment_spec.benchmark_split or run_spec.benchmark_split or "guided")
    root = str((run_spec.environment or {}).get("cybench_root") or "references/cybench")
    args = Namespace(
        workspace=str((run_spec.environment or {}).get("workspace") or "./playground/cybench"),
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
        max_steps=int((run_spec.metadata or {}).get("max_steps", 12)),
        cybench_root=root,
        trials=1,
        easy_prompt=False,
        unguided_mode=bool(split_mode == "unguided"),
        run_requirements=False,
        start_docker=False,
        script_timeout=300,
        use_docker_env=False,
        docker_image="python:3.11-slim",
        docker_network="",
        container_workspace="/workspace",
        split_mode=split_mode,
    )
    args.adapter = CyBenchAdapter(
        cybench_root=root,
        run_with_subtasks=not bool(args.unguided_mode),
    )
    return args
