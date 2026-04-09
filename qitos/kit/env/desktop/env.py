"""OSWorld-inspired desktop environment for QitOS."""

from __future__ import annotations

from typing import Any, Dict, Optional

from qitos.core import Env, EnvObservation, EnvStepResult
from qitos.core.multimodal import EnvironmentAdapter, normalize_observation_pack

from .actions import desktop_action_space, normalize_gui_action, validate_gui_action
from .controller import DesktopControllerOps, DesktopObserverOps
from .providers import ContainerDesktopProvider, DesktopProvider, MockDesktopProvider


class DesktopEnv(Env, EnvironmentAdapter):
    """Desktop environment with screenshot, a11y, terminal, and GUI control support."""

    name = "desktop_env"
    version = "0.5"

    def __init__(self, provider: DesktopProvider):
        self.provider = provider
        self.observer = DesktopObserverOps(provider)
        self.controller = DesktopControllerOps(provider)
        self._action_space = desktop_action_space()
        self._last_observation: Optional[EnvObservation] = None

    @classmethod
    def from_mock(
        cls,
        *,
        screenshot_path: str,
        instruction: str = "",
        accessibility_tree: Any = None,
        terminal: str = "",
        dom: Any = None,
        ocr: Optional[list[dict[str, Any]]] = None,
        ui_candidates: Optional[list[dict[str, Any]]] = None,
        screen_size: tuple[int, int] = (1920, 1080),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DesktopEnv":
        return cls(
            MockDesktopProvider(
                screenshot_path=screenshot_path,
                instruction=instruction,
                accessibility_tree=accessibility_tree,
                terminal=terminal,
                dom=dom,
                ocr=ocr,
                ui_candidates=ui_candidates,
                screen_size=screen_size,
                metadata=metadata,
            )
        )

    @classmethod
    def from_container(
        cls,
        *,
        container: str,
        screenshot_path: str,
        workspace_root: str = "/workspace",
        controller_endpoint: str = "",
        instruction: str = "",
        accessibility_tree: Any = None,
        terminal: str = "",
        dom: Any = None,
        ocr: Optional[list[dict[str, Any]]] = None,
        ui_candidates: Optional[list[dict[str, Any]]] = None,
        screen_size: tuple[int, int] = (1920, 1080),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DesktopEnv":
        return cls(
            ContainerDesktopProvider(
                container=container,
                screenshot_path=screenshot_path,
                workspace_root=workspace_root,
                controller_endpoint=controller_endpoint,
                instruction=instruction,
                accessibility_tree=accessibility_tree,
                terminal=terminal,
                dom=dom,
                ocr=ocr,
                ui_candidates=ui_candidates,
                screen_size=screen_size,
                metadata=metadata,
            )
        )

    def setup(
        self, task: Any = None, workspace: Optional[str] = None, **kwargs: Any
    ) -> None:
        _ = task
        _ = workspace
        _ = kwargs
        self.provider.start()

    def reset(
        self, task: Any = None, workspace: Optional[str] = None, **kwargs: Any
    ) -> EnvObservation:
        self.provider.reset(task=task, workspace=workspace)
        return self.observe()

    def observe(self, state: Any = None) -> EnvObservation:
        payload = self.observer.capture_observation(state=state)
        pack = normalize_observation_pack(payload)
        metadata = {
            "modalities": ["desktop", "screenshot"],
            "provider": getattr(self.provider, "name", self.provider.__class__.__name__),
        }
        if pack is not None and isinstance(pack.metadata, dict):
            screen_size = pack.metadata.get("screen_size")
            if screen_size is not None:
                metadata["screen_size"] = screen_size
        observation = EnvObservation(
            data={
                "multimodal": payload,
                "desktop": {
                    "instruction": (pack.metadata.get("instruction") if pack and isinstance(pack.metadata, dict) else None),
                    "terminal": (pack.metadata.get("terminal") if pack and isinstance(pack.metadata, dict) else None),
                    "screen_size": (pack.metadata.get("screen_size") if pack and isinstance(pack.metadata, dict) else None),
                    "provider": getattr(self.provider, "name", self.provider.__class__.__name__),
                },
            },
            metadata=metadata,
        )
        self._last_observation = observation
        return observation

    def capabilities(self) -> Dict[str, Any]:
        screen_size = None
        if self._last_observation is not None:
            screen_size = (
                (self._last_observation.data.get("desktop") or {}).get("screen_size")
                if isinstance(self._last_observation.data, dict)
                else None
            )
        return {
            "gui_observer": True,
            "gui_controller": True,
            "provider": getattr(self.provider, "name", self.provider.__class__.__name__),
            "screen_size": screen_size,
        }

    def action_space(self):
        return self._action_space

    def step(self, action: Any, state: Any = None) -> EnvStepResult:
        performed: list[dict[str, Any]] = []
        validation_errors: list[dict[str, Any]] = []
        if isinstance(action, dict):
            raw_actions = action.get("actions")
            if isinstance(raw_actions, list):
                for item in raw_actions:
                    if isinstance(item, dict):
                        normalized = normalize_gui_action(item)
                        if normalized.get("action_type"):
                            validation = validate_gui_action(normalized)
                            if not bool(validation.get("ok", False)):
                                validation_errors.append(
                                    {
                                        "action": normalized,
                                        "errors": list(validation.get("errors") or []),
                                    }
                                )
                                performed.append(
                                    {
                                        "status": "validation_error",
                                        "execution_state": "failed",
                                        "provider": getattr(
                                            self.provider,
                                            "name",
                                            self.provider.__class__.__name__,
                                        ),
                                        "action": normalized,
                                        "message": "; ".join(
                                            str(x)
                                            for x in (validation.get("errors") or [])
                                        ),
                                    }
                                )
                                continue
                            review_required = bool(
                                ((normalized.get("metadata") or {}).get("requires_approval"))
                                or (
                                    str(normalized.get("action_type") or "")
                                    in {"type_text", "hotkey", "press_key"}
                                    and bool(
                                        (normalized.get("metadata") or {}).get(
                                            "sensitive"
                                        )
                                    )
                                )
                            )
                            if review_required:
                                performed.append(
                                    {
                                        "status": "approval_required",
                                        "execution_state": "approval_required",
                                        "provider": getattr(
                                            self.provider,
                                            "name",
                                            self.provider.__class__.__name__,
                                        ),
                                        "action": normalized,
                                        "message": "Action requires human review before execution.",
                                    }
                                )
                                continue
                            performed.append(
                                self.controller.perform(normalized, state=state)
                            )
        observation = self.observe(state=state)
        done = False
        if isinstance(action, dict):
            if str(action.get("decision_mode") or "") == "final":
                done = True
            elif any(
                str((result.get("action") or {}).get("action_type") or "") in {"done", "fail"}
                for result in performed
                if isinstance(result, dict)
            ):
                done = True
        return EnvStepResult(
            observation=observation,
            done=done,
            info={
                "performed_actions": performed,
                "validation_errors": validation_errors,
                "capabilities": self.capabilities(),
                "action_space": self.action_space().to_dict(),
            },
        )

    def get_ops(self, group: str) -> Any:
        name = str(group or "").strip().lower()
        if name == "gui_observer":
            return self.observer
        if name == "gui_controller":
            return self.controller
        return None

    def health_check(self) -> Dict[str, Any]:
        return dict(self.provider.health_check() or {})

    def close(self) -> None:
        self.provider.stop()


__all__ = ["DesktopEnv"]
