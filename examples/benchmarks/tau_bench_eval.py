"""Thin Tau-Bench benchmark example entrypoint backed by the canonical recipe."""

from qitos.recipes.benchmarks.tau_bench import (
    DEFAULT_MODEL_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_THEME,
    TauActionTool,
    TauBenchAgent,
    TauRecipeExecution,
    TauState,
    build_tau_benchmark_result,
    build_tau_env,
    evaluate_tau_result,
    execute_tau_task,
    main,
    run_tau_recipe_task,
)

__all__ = [
    "DEFAULT_MODEL_BASE_URL",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_THEME",
    "TauActionTool",
    "TauBenchAgent",
    "TauRecipeExecution",
    "TauState",
    "build_tau_benchmark_result",
    "build_tau_env",
    "evaluate_tau_result",
    "execute_tau_task",
    "main",
    "run_tau_recipe_task",
]


if __name__ == "__main__":
    main()
