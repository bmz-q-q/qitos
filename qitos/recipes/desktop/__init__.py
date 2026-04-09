"""Desktop and computer-use recipes for QitOS."""

from .osworld_starter import (
    DEFAULT_MODEL_FAMILY,
    DEFAULT_OBSERVATION_MODE,
    DEFAULT_PROTOCOL,
    DesktopBaselineExecution,
    DesktopGroundingCritic,
    OpenAICUAAgent,
    OpenAICUAState,
    build_agent,
    build_benchmark_result,
    build_desktop_critics,
    build_task,
    configure_runtime_for_task,
    execute_desktop_task,
    main,
)

__all__ = [
    "DEFAULT_MODEL_FAMILY",
    "DEFAULT_OBSERVATION_MODE",
    "DEFAULT_PROTOCOL",
    "DesktopBaselineExecution",
    "DesktopGroundingCritic",
    "OpenAICUAAgent",
    "OpenAICUAState",
    "build_agent",
    "build_benchmark_result",
    "build_desktop_critics",
    "build_task",
    "configure_runtime_for_task",
    "execute_desktop_task",
    "main",
]
