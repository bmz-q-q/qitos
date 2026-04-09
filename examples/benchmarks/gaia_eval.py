"""Thin GAIA benchmark example entrypoint backed by the canonical recipe."""

from qitos.recipes.benchmarks.gaia import (
    DEFAULT_MODEL_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_THEME,
    GaiaRecipeExecution,
    ODRGaiaState,
    OpenDeepResearchGaiaAgent,
    build_gaia_benchmark_result,
    build_gaia_task,
    execute_gaia_task,
    main,
    run_gaia_recipe_task,
)

__all__ = [
    "DEFAULT_MODEL_BASE_URL",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_THEME",
    "GaiaRecipeExecution",
    "ODRGaiaState",
    "OpenDeepResearchGaiaAgent",
    "build_gaia_benchmark_result",
    "build_gaia_task",
    "execute_gaia_task",
    "main",
    "run_gaia_recipe_task",
]


if __name__ == "__main__":
    main()
