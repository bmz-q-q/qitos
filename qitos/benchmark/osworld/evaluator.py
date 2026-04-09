"""OSWorld post-run evaluator bridge that loads upstream reference metrics/getters."""

from __future__ import annotations

import importlib.util
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlparse

from qitos.core import ExperimentSpec, RunSpec

from ..contracts import BenchmarkEvaluator, PreparedBenchmarkTask


_FUNC_CACHE: dict[tuple[str, str, str], Callable[..., Any]] = {}


@dataclass
class _EvalContext:
    controller: Any
    vm_ip: str
    server_port: int
    cache_dir: str
    evaluator: Mapping[str, Any]
    action_history: list[Any]
    enable_proxy: bool = False

    @property
    def vm_platform(self) -> Any:
        try:
            return self.controller.get_vm_platform()
        except Exception:
            return None

    @property
    def vm_screen_size(self) -> Any:
        try:
            return self.controller.get_vm_screen_size()
        except Exception:
            return None


def _reference_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "references" / "OSWorld"


def _ensure_import_path(root: str | Path | None = None) -> Path:
    ref_root = _reference_root(root)
    if not ref_root.exists():
        raise FileNotFoundError(f"OSWorld reference path not found: {ref_root}")
    root_str = str(ref_root.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return ref_root


def _ensure_namespace_package(package_name: str, package_path: Path) -> types.ModuleType:
    path_str = str(package_path.resolve())
    existing = sys.modules.get(package_name)
    if existing is None:
        module = types.ModuleType(package_name)
        module.__package__ = package_name
        module.__file__ = str((package_path / "__init__.py").resolve())
        module.__path__ = [path_str]  # type: ignore[attr-defined]
        sys.modules[package_name] = module
        return module
    paths = list(getattr(existing, "__path__", []))
    if path_str not in paths:
        existing.__path__ = [path_str, *paths]  # type: ignore[attr-defined]
    return existing


def _load_module_from_file(*, module_name: str, module_file: Path) -> types.ModuleType:
    cached = sys.modules.get(module_name)
    if isinstance(cached, types.ModuleType):
        return cached
    spec = importlib.util.spec_from_file_location(module_name, str(module_file.resolve()))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {module_name} from {module_file}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _load_callable(*, reference_root: str | Path | None, category: str, func_name: str) -> Callable[..., Any]:
    root = str(_reference_root(reference_root))
    key = (root, category, func_name)
    cached = _FUNC_CACHE.get(key)
    if cached is not None:
        return cached

    ref_root = _ensure_import_path(reference_root)
    base = ref_root / "desktop_env" / "evaluators" / category
    if not base.exists():
        raise FileNotFoundError(f"OSWorld evaluator category path not found: {base}")

    pattern = re.compile(rf"^\s*def\s+{re.escape(func_name)}\s*\(", re.MULTILINE)
    target_module: str | None = None
    target_file: Path | None = None
    for py_file in sorted(base.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            target_module = f"desktop_env.evaluators.{category}.{py_file.stem}"
            target_file = py_file
            break
    if not target_module or target_file is None:
        raise AttributeError(f"OSWorld {category} function not found: {func_name}")

    desktop_env_root = ref_root / "desktop_env"
    evaluators_root = desktop_env_root / "evaluators"
    _ensure_namespace_package("desktop_env", desktop_env_root)
    _ensure_namespace_package("desktop_env.evaluators", evaluators_root)
    _ensure_namespace_package(f"desktop_env.evaluators.{category}", base)
    module = _load_module_from_file(module_name=target_module, module_file=target_file)
    fn = getattr(module, func_name, None)
    if not callable(fn):
        raise AttributeError(f"OSWorld {category} function not callable: {func_name}")
    _FUNC_CACHE[key] = fn
    return fn


def _load_metric(*, reference_root: str | Path | None, func_name: str) -> Callable[..., Any]:
    return _load_callable(reference_root=reference_root, category="metrics", func_name=func_name)


def _load_getter(*, reference_root: str | Path | None, getter_type: str) -> Callable[..., Any]:
    return _load_callable(
        reference_root=reference_root,
        category="getters",
        func_name=f"get_{getter_type}",
    )


def resolve_eval_cache_dir(
    *,
    eval_cache_dir: str | None,
    eval_cache_root: str | Path,
    sample_id: str | None,
    task_id: str | None,
) -> Path:
    explicit = str(eval_cache_dir or "").strip()
    if explicit:
        path = Path(explicit)
    else:
        token = str(sample_id or task_id or "default")
        token = re.sub(r"[<>:\"/\\|?*\x00-\x1f]+", "_", token).strip(" ._") or "default"
        path = Path(eval_cache_root) / token
    path.mkdir(parents=True, exist_ok=True)
    return path


def evaluate_task(
    *,
    endpoint: str,
    evaluator: Mapping[str, Any],
    action_history: Sequence[Any],
    proxy: bool = False,
    sample_id: str | None = None,
    task_id: str | None = None,
    eval_cache_root: str | Path = ".qitos/osworld_eval_cache",
    eval_cache_dir: str | None = None,
    reference_root: str | Path | None = None,
) -> dict[str, Any]:
    if not isinstance(evaluator, Mapping):
        raise ValueError("Missing evaluator config in payload.")
    if not endpoint:
        raise ValueError("Missing controller endpoint for OSWorld evaluation.")

    parsed = urlparse(endpoint)
    vm_ip = parsed.hostname or "localhost"
    server_port = int(parsed.port or 80)
    cache_dir = resolve_eval_cache_dir(
        eval_cache_dir=eval_cache_dir,
        eval_cache_root=eval_cache_root,
        sample_id=sample_id,
        task_id=task_id,
    )
    postconfig = list(evaluator.get("postconfig") or [])
    postconfig_results: list[dict[str, Any]] = []
    if postconfig:
        from .runtime import run_setup_config

        postconfig_results = run_setup_config(endpoint=endpoint, setup_config=postconfig)

    metric_cfg = evaluator.get("func")
    if not isinstance(metric_cfg, str) or not metric_cfg.strip():
        return {
            "event": "gui.evaluate",
            "score": 0.0,
            "simulated": True,
            "error": "missing metric function",
            "mode": "osworld_evaluator_fallback",
            "postconfig": postconfig_results,
        }

    controller = types.SimpleNamespace(
        endpoint=endpoint,
        get_vm_platform=lambda: None,
        get_vm_screen_size=lambda: None,
    )
    context = _EvalContext(
        controller=controller,
        vm_ip=vm_ip,
        server_port=server_port,
        cache_dir=str(cache_dir),
        evaluator=evaluator,
        action_history=list(action_history),
        enable_proxy=bool(proxy),
    )

    metric = _load_metric(reference_root=reference_root, func_name=metric_cfg)
    getter_type = str(evaluator.get("result_getter") or "").strip()
    getter_result = None
    try:
        _ensure_import_path(reference_root)
        from desktop_env.controllers.python import PythonController  # type: ignore[import-not-found]

        controller = PythonController(vm_ip=vm_ip, server_port=server_port)
        context.controller = controller
    except Exception:
        pass
    if getter_type:
        getter = _load_getter(reference_root=reference_root, getter_type=getter_type)
        getter_result = getter(context)
        score_raw = metric(getter_result, context)
    else:
        score_raw = metric(context)
    try:
        score = float(score_raw)
    except Exception:
        score = 0.0
    return {
        "event": "gui.evaluate",
        "score": max(0.0, min(1.0, score)),
        "simulated": False,
        "error": None,
        "mode": "osworld_evaluator",
        "metric": metric_cfg,
        "getter": getter_type or None,
        "getter_result": getter_result,
        "postconfig": postconfig_results,
        "cache_dir": str(cache_dir),
    }


class OSWorldEvaluator(BenchmarkEvaluator):
    def __init__(
        self,
        *,
        reference_root: str | Path | None = None,
        eval_cache_root: str | Path = ".qitos/osworld_eval_cache",
    ) -> None:
        self.reference_root = str(reference_root) if reference_root is not None else None
        self.eval_cache_root = str(eval_cache_root)

    def evaluate(
        self,
        *,
        prepared: PreparedBenchmarkTask,
        run_spec: RunSpec,
        experiment_spec: ExperimentSpec,
        execution: Any,
    ) -> dict[str, Any]:
        _ = experiment_spec
        evaluator_cfg = (prepared.task.metadata or {}).get("evaluator")
        if not isinstance(evaluator_cfg, Mapping):
            return {
                "event": "gui.evaluate",
                "score": 0.0,
                "simulated": True,
                "error": "missing evaluator config",
                "mode": "osworld_evaluator_fallback",
            }
        runtime_prepare = dict((prepared.runtime_metadata or {}).get("runtime_prepare") or {})
        endpoint = str(runtime_prepare.get("controller_endpoint") or "")
        records = list(getattr(execution.result, "records", []) or [])
        action_history: list[dict[str, Any]] = []
        for record in records:
            for action in list(getattr(record, "actions", []) or []):
                if hasattr(action, "to_dict"):
                    action_history.append(action.to_dict())
                elif isinstance(action, dict):
                    action_history.append(dict(action))
        return evaluate_task(
            endpoint=endpoint,
            evaluator=dict(evaluator_cfg),
            action_history=action_history,
            proxy=bool((prepared.task.metadata or {}).get("proxy", False)),
            sample_id=str((prepared.task.metadata or {}).get("example_id") or prepared.task.id),
            task_id=str(prepared.task.id),
            eval_cache_root=self.eval_cache_root,
            eval_cache_dir=str((run_spec.environment or {}).get("osworld_eval_cache_dir") or ""),
            reference_root=self.reference_root,
        )


__all__ = [
    "OSWorldEvaluator",
    "evaluate_task",
    "resolve_eval_cache_dir",
]
