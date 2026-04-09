"""Thin CyBench benchmark example entrypoint backed by the canonical recipe."""

from qitos.recipes.benchmarks.cybench import (
    DEFAULT_MODEL_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_THEME,
    CyBenchReactAgent,
    CyBenchRecipeExecution,
    CyBenchState,
    build_cybench_benchmark_result,
    execute_cybench_task,
    main,
    run_cybench_recipe_task,
)

__all__ = [
    "DEFAULT_MODEL_BASE_URL",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_THEME",
    "CyBenchReactAgent",
    "CyBenchRecipeExecution",
    "CyBenchState",
    "build_cybench_benchmark_result",
    "execute_cybench_task",
    "main",
    "run_cybench_recipe_task",
]


if __name__ == "__main__":
    main()
