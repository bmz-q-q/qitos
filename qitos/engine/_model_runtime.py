"""Private model/runtime helpers for Engine."""

from __future__ import annotations

from typing import Any, Dict, Generic, List, TypeVar

from ..core.decision import Decision
from ..core.errors import ErrorCategory, ParseExecutionError, RuntimeErrorInfo
from ..core.state import StateSchema
from ._context_runtime import ContextOverflowError
from .states import RuntimePhase, StepRecord


StateT = TypeVar("StateT", bound=StateSchema)
ObservationT = TypeVar("ObservationT")
ActionT = TypeVar("ActionT")


class _ModelRuntime(Generic[StateT, ObservationT, ActionT]):
    def __init__(self, engine: Any):
        self.engine = engine

    def run_decide(self, state: StateT, observation: ObservationT, record: StepRecord) -> Decision[ActionT]:
        engine = self.engine
        engine._dispatch_hook(
            "on_before_decide",
            engine._hook_context(
                step_id=record.step_id,
                phase=RuntimePhase.DECIDE,
                state=state,
                observation=observation,
                record=record,
            ),
        )
        engine._emit(record.step_id, RuntimePhase.DECIDE, payload={"stage": "state_ready", "observation": observation})
        engine._memory_append("state", state.to_dict(), record.step_id)
        engine._emit(record.step_id, RuntimePhase.DECIDE, payload={"stage": "start"})
        raw_decision = engine.agent.decide(state, observation)
        if raw_decision is None:
            raw_decision = self._run_llm_decide(state=state, observation=observation, record=record)

        decision = self.normalize_decision(raw_decision, step=record.step_id)
        if decision.mode == "branch":
            decision = self.select_branch(state, observation, decision)

        if decision.mode not in {"act", "final", "wait"}:
            raise ValueError(f"Invalid decision mode: {decision.mode}")

        decision.validate()
        record.decision = decision
        record.actions = list(decision.actions)
        engine._memory_append("decision", decision, record.step_id)
        engine._emit(
            record.step_id,
            RuntimePhase.DECIDE,
            payload={
                "stage": "decision_ready",
                "mode": decision.mode,
                "rationale": decision.rationale,
                "actions": decision.actions,
                "final_answer": decision.final_answer,
                "candidate_count": len(decision.candidates),
            },
        )
        engine._dispatch_hook(
            "on_after_decide",
            engine._hook_context(
                step_id=record.step_id,
                phase=RuntimePhase.DECIDE,
                state=state,
                observation=observation,
                decision=decision,
                record=record,
            ),
        )
        return decision

    def _run_llm_decide(self, state: StateT, observation: ObservationT, record: StepRecord) -> Any:
        engine = self.engine
        if engine.agent.llm is None:
            raise ValueError("No llm configured and Agent.decide returned None")
        setattr(engine.agent, "_runtime_observation", observation)
        setattr(engine.agent, "_runtime_step_id", record.step_id)
        try:
            prepared = engine.agent.prepare(state)
        finally:
            if hasattr(engine.agent, "_runtime_observation"):
                delattr(engine.agent, "_runtime_observation")
            if hasattr(engine.agent, "_runtime_step_id"):
                delattr(engine.agent, "_runtime_step_id")
        system_prompt = engine.agent.build_system_prompt(state)
        context_runtime = engine._context_runtime
        pre_context = context_runtime.build_pre_request(
            llm=engine.agent.llm,
            system_prompt=system_prompt if isinstance(system_prompt, str) else "",
            prepared=str(prepared),
        )
        messages: List[Dict[str, str]] = []
        if isinstance(system_prompt, str) and system_prompt.strip():
            system = system_prompt.strip()
            messages.append({"role": "system", "content": system})
            if system != engine._last_system_prompt:
                engine._history_append("system", system, record.step_id, metadata={"source": "engine"})
                engine._last_system_prompt = system
        history: List[Dict[str, str]] = []
        query = engine.history_policy.build_query(
            step_id=record.step_id,
            phase=RuntimePhase.DECIDE.value,
            query_kind="decide",
        )
        if isinstance(query, dict):
            query.setdefault("pending_content", str(prepared))
            query.setdefault("model_name", getattr(getattr(engine.agent, "llm", None), "model", None))
            query.setdefault("step_id", record.step_id)
            query.setdefault("warning_ratio", float(engine.context_config.warning_ratio))
            history_budget = context_runtime.history_budget(pre_context)
            if history_budget is not None:
                current_max = query.get("max_tokens")
                if current_max is None:
                    query["max_tokens"] = history_budget
                else:
                    try:
                        query["max_tokens"] = min(int(current_max), int(history_budget))
                    except Exception:
                        query["max_tokens"] = history_budget
        try:
            history_impl = engine._history()
            retrieved = history_impl.retrieve(state=state, observation=observation, query=query)
            history = engine._normalize_history_messages(retrieved)
            compact_events = []
            consume_runtime_events = getattr(history_impl, "consume_runtime_events", None)
            if callable(consume_runtime_events):
                compact_events = list(consume_runtime_events() or [])
            history_metadata = []
            get_last_message_metadata = getattr(history_impl, "get_last_message_metadata", None)
            if callable(get_last_message_metadata):
                history_metadata = list(get_last_message_metadata() or [])
        except Exception:
            history = []
            history_metadata = []
            compact_events = []
        pre_context = context_runtime.finalize_input(
            llm=engine.agent.llm,
            telemetry=pre_context,
            history_messages=history,
            compact_events=compact_events,
        )
        normalized_compact_events = context_runtime.normalize_history_events(compact_events, pre_context)
        if not normalized_compact_events:
            warning_event = context_runtime.maybe_note_warning(pre_context)
            if warning_event is not None:
                normalized_compact_events = [warning_event]
        for compact_event in normalized_compact_events:
            engine._emit(record.step_id, RuntimePhase.DECIDE, payload=compact_event)
        if context_runtime.should_overflow(pre_context):
            engine._emit(record.step_id, RuntimePhase.DECIDE, payload=context_runtime.overflow_event(pre_context))
            raise ContextOverflowError(
                f"context overflow: input_tokens={pre_context.input_tokens_total} budget={pre_context.available_input_budget}"
            )
        current_user = {"role": "user", "content": str(prepared)}
        messages.extend(history)
        messages.append(current_user)
        record.context = context_runtime.telemetry_dict(pre_context)
        engine._last_context_telemetry = dict(record.context)
        engine._emit(
            record.step_id,
            RuntimePhase.DECIDE,
            payload={
                "stage": "model_input",
                "prepared": str(prepared),
                "history_message_count": len(history),
                "history_messages_meta": history_metadata,
                "messages": messages,
                "context": dict(record.context),
                "state_stats": self._state_stats(observation, record.context),
            },
        )
        engine._history_append("user", str(prepared), record.step_id, metadata={"source": "engine"})
        raw_decision = engine.agent.llm(messages)
        post_context = context_runtime.finalize_output(
            llm=engine.agent.llm,
            telemetry=pre_context,
            raw_output=str(raw_decision),
        )
        record.context = context_runtime.telemetry_dict(post_context)
        engine._last_context_telemetry = dict(record.context)
        engine._emit(
            record.step_id,
            RuntimePhase.DECIDE,
            payload={"stage": "model_output", "raw_output": str(raw_decision), "context": dict(record.context)},
        )
        engine._history_append("assistant", str(raw_decision), record.step_id, metadata={"source": "engine"})
        return raw_decision

    def _state_stats(self, observation: ObservationT, context: Dict[str, Any]) -> Dict[str, Any]:
        stats: Dict[str, Any] = {}
        if isinstance(observation, dict):
            scratchpad = observation.get("scratchpad")
            if isinstance(scratchpad, list):
                stats["scratchpad_items"] = len(scratchpad)
            elif isinstance(scratchpad, str) and scratchpad.strip():
                stats["scratchpad_items"] = 1
            memory = observation.get("memory")
            if isinstance(memory, dict) and isinstance(memory.get("records"), list):
                stats["memory_records"] = len(memory.get("records") or [])
            workspace_files = observation.get("workspace_files")
            if isinstance(workspace_files, list):
                stats["workspace_files"] = len(workspace_files)
        for key in ("input_tokens_total", "history_tokens", "output_tokens", "occupancy_ratio", "context_window"):
            if key in context:
                stats[key] = context.get(key)
        return stats

    def select_branch(
        self,
        state: StateT,
        observation: ObservationT,
        branch_decision: Decision[ActionT],
    ) -> Decision[ActionT]:
        engine = self.engine
        if engine.search is not None:
            candidates = engine.search.expand(state, observation, branch_decision) or list(branch_decision.candidates)
            scores = engine.search.score(state, observation, candidates)
            candidates = engine.search.prune(candidates, scores)
            if not candidates:
                new_state = engine.search.backtrack(state)
                if new_state is not state:
                    state.__dict__.update(new_state.__dict__)
                return Decision.wait(rationale="search backtrack")
            scores = engine.search.score(state, observation, candidates)
            selected = engine.search.select(candidates, scores)
            mark_selected = getattr(engine.search, "mark_selected", None)
            if callable(mark_selected):
                mark_selected(state, selected)
        else:
            selected = engine.branch_selector.select(branch_decision.candidates, state, observation)
        selected.validate()
        return selected

    def normalize_decision(self, raw_decision: Any, step: int) -> Decision[ActionT]:
        if isinstance(raw_decision, Decision):
            return raw_decision

        parser = self.engine.parser or getattr(self.engine.agent, "model_parser", None)
        if parser is not None:
            try:
                return parser.parse(raw_decision, context={"step": step})
            except Exception as exc:
                info = RuntimeErrorInfo(
                    category=ErrorCategory.PARSE,
                    message=str(exc),
                    phase="decide",
                    step_id=step,
                    recoverable=True,
                )
                raise ParseExecutionError(info) from exc

        raise ValueError("Agent.decide must return Decision when no parser is configured")
